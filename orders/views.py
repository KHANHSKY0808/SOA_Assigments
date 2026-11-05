from decimal import Decimal
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Order, OrderItem
from .serializers import OrderDetailSerializer, OrderItemSerializer
from .authentication import ExternalTokenAuthentication
from .services import get_product_info, update_product_stock


class OrderListCreateAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # GET /orders: Lấy danh sách tất cả các đơn hàng
    def get(self, request):
        status_param = request.query_params.get('status')
        orders = Order.objects.all().order_by('-id')
        if status_param:
            orders = orders.filter(status=status_param)
        serializer = OrderDetailSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /orders: Tạo đơn hàng mới (kiểm tra tồn kho qua Product Service)
    def post(self, request):
        data = request.data
        customer_name = data.get('customer_name')
        customer_email = data.get('customer_email')
        order_status = data.get('status', Order.STATUS_PENDING)
        items_data = data.get('items', [])

        if not customer_name or not customer_email:
            return Response(
                {"error": "Vui lòng cung cấp đầy đủ 'customer_name' và 'customer_email'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_token = getattr(request, 'auth', None)

        # 1. Kiểm tra tồn kho trước khi tạo đơn hàng
        validated_items = []
        if items_data:
            if not isinstance(items_data, list):
                return Response(
                    {"error": "Trường 'items' phải là một danh sách các mặt hàng"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for item_input in items_data:
                product_id = item_input.get('product_id')
                quantity = item_input.get('quantity', 1)

                if not product_id:
                    return Response(
                        {"error": "Mỗi mặt hàng cần có 'product_id'"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    quantity = int(quantity)
                    if quantity <= 0:
                        return Response(
                            {"error": f"Số lượng của sản phẩm ID {product_id} phải lớn hơn 0"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except (ValueError, TypeError):
                    return Response(
                        {"error": f"Số lượng của sản phẩm ID {product_id} không hợp lệ"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Kiểm tra tồn kho qua Product Service
                product_info = get_product_info(product_id, auth_token)
                if not product_info:
                    return Response(
                        {"error": f"Không tìm thấy sản phẩm với ID {product_id} từ Product Service"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                available_stock = product_info['quantity']
                if available_stock < quantity:
                    return Response(
                        {
                            "error": f"Sản phẩm '{product_info['name']}' (ID: {product_id}) không đủ tồn kho. "
                                     f"Hiện còn: {available_stock}, yêu cầu: {quantity}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                unit_price = Decimal(str(item_input.get('unit_price') or product_info['price']))
                product_name = item_input.get('product_name') or product_info['name']
                total_price = unit_price * quantity

                validated_items.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price,
                    'available_stock': available_stock,
                })

        # 2. Tạo đơn hàng và trừ tồn kho trong Database Transaction
        with transaction.atomic():
            order = Order.objects.create(
                customer_name=customer_name,
                customer_email=customer_email,
                status=order_status,
                total_amount=Decimal('0.00')
            )

            total_amount = Decimal('0.00')
            for item in validated_items:
                OrderItem.objects.create(
                    order=order,
                    product_id=item['product_id'],
                    product_name=item['product_name'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    total_price=item['total_price']
                )
                total_amount += item['total_price']

                # Cập nhật trừ tồn kho trong Product Service
                new_stock = item['available_stock'] - item['quantity']
                update_product_stock(item['product_id'], new_stock, auth_token)

            order.total_amount = total_amount
            order.save()

        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return None

    # GET /orders/<id>: Lấy thông tin chi tiết một đơn hàng
    def get(self, request, pk):
        order = self.get_object(pk)
        if not order:
            return Response({"error": "Không tìm thấy đơn hàng"}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT /orders/<id>: Cập nhật trạng thái đơn hàng
    def put(self, request, pk):
        order = self.get_object(pk)
        if not order:
            return Response({"error": "Không tìm thấy đơn hàng"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {"error": "Vui lòng cung cấp trường 'status' cần cập nhật"},
                status=status.HTTP_400_BAD_REQUEST
            )

        valid_statuses = [Order.STATUS_PENDING, Order.STATUS_COMPLETED, Order.STATUS_CANCELLED]
        if new_status not in valid_statuses:
            return Response(
                {"error": f"Trạng thái không hợp lệ. Các trạng thái hợp lệ: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_token = getattr(request, 'auth', None)

        with transaction.atomic():
            # Nếu chuyển sang hủy (cancelled), hoàn trả tồn kho cho các sản phẩm
            if new_status == Order.STATUS_CANCELLED and order.status != Order.STATUS_CANCELLED:
                for item in order.items.all():
                    prod_info = get_product_info(item.product_id, auth_token)
                    if prod_info:
                        current_stock = prod_info['quantity']
                        update_product_stock(item.product_id, current_stock + item.quantity, auth_token)

            order.status = new_status
            if 'customer_name' in request.data:
                order.customer_name = request.data['customer_name']
            if 'customer_email' in request.data:
                order.customer_email = request.data['customer_email']

            order.save()

        serializer = OrderDetailSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DELETE /orders/<id>: Xóa một đơn hàng
    def delete(self, request, pk):
        order = self.get_object(pk)
        if not order:
            return Response({"error": "Không tìm thấy đơn hàng"}, status=status.HTTP_404_NOT_FOUND)

        auth_token = getattr(request, 'auth', None)

        with transaction.atomic():
            # Nếu đơn hàng bị xóa khi chưa hủy, hoàn lại số lượng tồn kho cho các mặt hàng
            if order.status != Order.STATUS_CANCELLED:
                for item in order.items.all():
                    prod_info = get_product_info(item.product_id, auth_token)
                    if prod_info:
                        current_stock = prod_info['quantity']
                        update_product_stock(item.product_id, current_stock + item.quantity, auth_token)

            order.delete()

        return Response({"message": "Đã xóa đơn hàng thành công"}, status=status.HTTP_204_NO_CONTENT)


class OrderItemListCreateAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # GET /order_items: Lấy danh sách tất cả mặt hàng trong đơn hàng
    def get(self, request):
        order_id = request.query_params.get('order_id')
        if order_id:
            items = OrderItem.objects.filter(order_id=order_id)
        else:
            items = OrderItem.objects.all()
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /order_items: Tạo mặt hàng mới
    def post(self, request):
        order_id = request.data.get('order_id')
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        if not order_id or not product_id:
            return Response(
                {"error": "Vui lòng cung cấp 'order_id' và 'product_id'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({"error": "Số lượng sản phẩm phải lớn hơn 0"}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({"error": "Số lượng không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return Response({"error": f"Không tìm thấy đơn hàng với ID {order_id}"}, status=status.HTTP_404_NOT_FOUND)

        if order.status == Order.STATUS_CANCELLED:
            return Response(
                {"error": "Không thể thêm mặt hàng vào đơn hàng đã bị hủy"},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_token = getattr(request, 'auth', None)

        # Kiểm tra tồn kho sản phẩm từ Product Service
        product_info = get_product_info(product_id, auth_token)
        if not product_info:
            return Response(
                {"error": f"Sản phẩm với ID {product_id} không tồn tại"},
                status=status.HTTP_404_NOT_FOUND
            )

        available_stock = product_info['quantity']
        if available_stock < quantity:
            return Response(
                {
                    "error": f"Sản phẩm '{product_info['name']}' (ID: {product_id}) không đủ tồn kho. "
                             f"Hiện còn: {available_stock}, yêu cầu: {quantity}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        unit_price = Decimal(str(request.data.get('unit_price') or product_info['price']))
        product_name = request.data.get('product_name') or product_info['name']
        total_price = unit_price * quantity

        with transaction.atomic():
            item = OrderItem.objects.create(
                order=order,
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price
            )

            # Trừ tồn kho
            update_product_stock(product_id, available_stock - quantity, auth_token)

            # Cập nhật tổng tiền đơn hàng
            order.total_amount = sum(i.total_price for i in order.items.all())
            order.save()

        serializer = OrderItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderItemDetailAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return OrderItem.objects.get(pk=pk)
        except OrderItem.DoesNotExist:
            return None

    # GET /order_items/<id>: Lấy thông tin chi tiết một mặt hàng
    def get(self, request, pk):
        item = self.get_object(pk)
        if not item:
            return Response({"error": "Không tìm thấy chi tiết mặt hàng"}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PUT /order_items/<id>: Cập nhật mặt hàng
    def put(self, request, pk):
        item = self.get_object(pk)
        if not item:
            return Response({"error": "Không tìm thấy chi tiết mặt hàng"}, status=status.HTTP_404_NOT_FOUND)

        auth_token = getattr(request, 'auth', None)
        new_quantity = request.data.get('quantity')
        new_unit_price = request.data.get('unit_price')
        new_product_name = request.data.get('product_name')

        with transaction.atomic():
            if new_quantity is not None:
                try:
                    new_quantity = int(new_quantity)
                    if new_quantity <= 0:
                        return Response({"error": "Số lượng phải lớn hơn 0"}, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({"error": "Số lượng không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)

                diff = new_quantity - item.quantity
                if diff > 0:
                    # Cần lấy thêm từ kho
                    prod_info = get_product_info(item.product_id, auth_token)
                    if not prod_info:
                        return Response({"error": "Không tìm thấy thông tin sản phẩm"}, status=status.HTTP_404_NOT_FOUND)
                    current_stock = prod_info['quantity']
                    if current_stock < diff:
                        return Response(
                            {
                                "error": f"Không đủ hàng trong kho để tăng thêm {diff} sản phẩm. Hiện có: {current_stock}"
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    update_product_stock(item.product_id, current_stock - diff, auth_token)
                elif diff < 0:
                    # Trả lại kho phần giảm bớt
                    prod_info = get_product_info(item.product_id, auth_token)
                    if prod_info:
                        current_stock = prod_info['quantity']
                        update_product_stock(item.product_id, current_stock + (-diff), auth_token)

                item.quantity = new_quantity

            if new_unit_price is not None:
                item.unit_price = Decimal(str(new_unit_price))

            if new_product_name is not None:
                item.product_name = new_product_name

            item.total_price = item.unit_price * item.quantity
            item.save()

            # Cập nhật tổng tiền đơn hàng
            order = item.order
            order.total_amount = sum(i.total_price for i in order.items.all())
            order.save()

        serializer = OrderItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DELETE /order_items/<id>: Xóa một mặt hàng trong đơn hàng
    def delete(self, request, pk):
        item = self.get_object(pk)
        if not item:
            return Response({"error": "Không tìm thấy chi tiết mặt hàng"}, status=status.HTTP_404_NOT_FOUND)

        auth_token = getattr(request, 'auth', None)
        order = item.order

        with transaction.atomic():
            # Hoàn lại tồn kho cho sản phẩm
            prod_info = get_product_info(item.product_id, auth_token)
            if prod_info:
                current_stock = prod_info['quantity']
                update_product_stock(item.product_id, current_stock + item.quantity, auth_token)

            item.delete()

            # Cập nhật lại tổng tiền đơn hàng
            order.total_amount = sum(i.total_price for i in order.items.all())
            order.save()

        return Response({"message": "Đã xóa mặt hàng thành công"}, status=status.HTTP_204_NO_CONTENT)
