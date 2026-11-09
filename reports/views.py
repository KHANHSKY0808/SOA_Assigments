from decimal import Decimal
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import OrderReport, ProductReport
from .serializers import OrderReportSerializer, ProductReportSerializer
from .authentication import ExternalTokenAuthentication
from .services import get_order_data, get_product_data, get_all_order_items_for_product


# ==============================================================================
# BÁO CÁO THEO SẢN PHẨM (PRODUCT REPORTS)
# ==============================================================================

class ProductReportListCreateAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # GET /reports/products: Lấy danh sách tất cả các báo cáo theo sản phẩm
    def get(self, request):
        reports = ProductReport.objects.all().order_by('-id')
        product_id = request.query_params.get('product_id')
        order_report_id = request.query_params.get('order_report_id')

        if product_id:
            reports = reports.filter(product_id=product_id)
        if order_report_id:
            reports = reports.filter(order_report_id=order_report_id)

        serializer = ProductReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /reports/products: Tạo báo cáo sản phẩm mới dựa trên dữ liệu từ Product Service & Order Service
    def post(self, request):
        data = request.data
        product_id = data.get('product_id')
        order_report_id = data.get('order_report_id')
        order_id = data.get('order_id')
        cost_input = data.get('cost')
        cost_per_unit = data.get('cost_per_unit')

        if not product_id:
            return Response(
                {"error": "Vui lòng cung cấp 'product_id' để tạo báo cáo sản phẩm"},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_token = getattr(request, 'auth', None)

        # 1. Kiểm tra sản phẩm từ Product Service
        product_data = get_product_data(product_id, auth_token)
        if not product_data:
            return Response(
                {"error": f"Không tìm thấy sản phẩm với ID {product_id} từ Product Service"},
                status=status.HTTP_404_NOT_FOUND
            )

        total_sold = 0
        revenue = Decimal('0.00')
        order_report_instance = None

        # 2. Xử lý dữ liệu bán hàng từ Order Service
        # Trường hợp 2.1: Báo cáo sản phẩm trong một OrderReport cụ thể
        if order_report_id:
            try:
                order_report_instance = OrderReport.objects.get(pk=order_report_id)
            except OrderReport.DoesNotExist:
                return Response(
                    {"error": f"Không tìm thấy báo cáo đơn hàng với ID {order_report_id}"},
                    status=status.HTTP_404_NOT_FOUND
                )

            order_data = get_order_data(order_report_instance.order_id, auth_token)
            if not order_data:
                return Response(
                    {"error": f"Không thể lấy thông tin đơn hàng #{order_report_instance.order_id} từ Order Service"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Tìm sản phẩm trong danh sách items của đơn hàng
            matching_items = [it for it in order_data.get('items', []) if it['product_id'] == int(product_id)]
            if not matching_items:
                return Response(
                    {"error": f"Sản phẩm ID {product_id} không tồn tại trong đơn hàng #{order_report_instance.order_id}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_sold = sum(it['quantity'] for it in matching_items)
            revenue = sum(it['total_price'] for it in matching_items)

        # Trường hợp 2.2: Báo cáo sản phẩm trong một Order cụ thể (truyền order_id)
        elif order_id:
            order_data = get_order_data(order_id, auth_token)
            if not order_data:
                return Response(
                    {"error": f"Không tìm thấy đơn hàng với ID {order_id} từ Order Service"},
                    status=status.HTTP_404_NOT_FOUND
                )

            matching_items = [it for it in order_data.get('items', []) if it['product_id'] == int(product_id)]
            if not matching_items:
                return Response(
                    {"error": f"Sản phẩm ID {product_id} không tồn tại trong đơn hàng #{order_id}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_sold = sum(it['quantity'] for it in matching_items)
            revenue = sum(it['total_price'] for it in matching_items)

            # Kiểm tra xem đơn hàng này đã có OrderReport chưa, nếu có thì liên kết
            order_report_instance = OrderReport.objects.filter(order_id=order_id).first()

        # Trường hợp 2.3: Báo cáo tổng hợp sản phẩm trên toàn bộ các đơn hàng
        else:
            all_items = get_all_order_items_for_product(product_id, auth_token)
            total_sold = sum(it['quantity'] for it in all_items)
            revenue = sum(it['total_price'] for it in all_items)

        # Cho phép ghi đè nếu client truyền trực tiếp total_sold hoặc revenue
        if 'total_sold' in data:
            try:
                total_sold = int(data['total_sold'])
            except (ValueError, TypeError):
                pass

        if 'revenue' in data:
            try:
                revenue = Decimal(str(data['revenue']))
            except Exception:
                pass

        # 3. Tính toán chi phí (Cost) và lợi nhuận (Profit)
        if cost_input is not None:
            try:
                cost = Decimal(str(cost_input))
            except Exception:
                return Response({"error": "Giá trị 'cost' không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)
        elif cost_per_unit is not None:
            try:
                cost = (Decimal(str(cost_per_unit)) * total_sold).quantize(Decimal('0.01'))
            except Exception:
                return Response({"error": "Giá trị 'cost_per_unit' không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Ước tính chi phí mặc định là 70% doanh thu (tỷ suất giá vốn chuẩn)
            cost = (revenue * Decimal('0.70')).quantize(Decimal('0.01'))

        profit = revenue - cost

        # 4. Lưu vào cơ sở dữ liệu
        product_report = ProductReport.objects.create(
            order_report=order_report_instance,
            product_id=product_id,
            total_sold=total_sold,
            revenue=revenue,
            cost=cost,
            profit=profit
        )

        serializer = ProductReportSerializer(product_report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductReportDetailDeleteAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return ProductReport.objects.get(pk=pk)
        except ProductReport.DoesNotExist:
            return None

    # GET /reports/products/<id>: Lấy chi tiết báo cáo cho một sản phẩm
    def get(self, request, pk):
        report = self.get_object(pk)
        if not report:
            return Response({"error": "Không tìm thấy báo cáo sản phẩm"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DELETE /reports/products/<id>: Xóa báo cáo sản phẩm
    def delete(self, request, pk):
        report = self.get_object(pk)
        if not report:
            return Response({"error": "Không tìm thấy báo cáo sản phẩm"}, status=status.HTTP_404_NOT_FOUND)
        report.delete()
        return Response({"message": "Đã xóa báo cáo sản phẩm thành công"}, status=status.HTTP_204_NO_CONTENT)


# ==============================================================================
# BÁO CÁO THEO ĐƠN HÀNG (ORDER REPORTS)
# ==============================================================================

class OrderReportListCreateAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # GET /reports/orders: Lấy danh sách tất cả các báo cáo theo đơn hàng
    def get(self, request):
        reports = OrderReport.objects.all().order_by('-id')
        order_id = request.query_params.get('order_id')
        if order_id:
            reports = reports.filter(order_id=order_id)
        serializer = OrderReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /reports/orders: Tạo báo cáo đơn hàng mới dựa trên dữ liệu từ dịch vụ quản lý đơn hàng
    def post(self, request):
        data = request.data
        order_id = data.get('order_id')
        cost_input = data.get('total_cost')
        cost_rate = data.get('cost_rate')
        auto_create_items = data.get('auto_create_product_reports', True)

        if not order_id:
            return Response(
                {"error": "Vui lòng cung cấp 'order_id' để tạo báo cáo đơn hàng"},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_token = getattr(request, 'auth', None)

        # 1. Lấy thông tin đơn hàng từ Order Service
        order_data = get_order_data(order_id, auth_token)
        if not order_data:
            return Response(
                {"error": f"Không tìm thấy đơn hàng với ID {order_id} từ Order Service"},
                status=status.HTTP_404_NOT_FOUND
            )

        total_revenue = Decimal(str(order_data.get('total_amount', '0.00')))

        # 2. Xử lý & tính toán chi phí (total_cost) và lợi nhuận (total_profit)
        if cost_input is not None:
            try:
                total_cost = Decimal(str(cost_input))
            except Exception:
                return Response({"error": "Giá trị 'total_cost' không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)
        elif cost_rate is not None:
            try:
                rate = Decimal(str(cost_rate))
                total_cost = (total_revenue * rate).quantize(Decimal('0.01'))
            except Exception:
                return Response({"error": "Giá trị 'cost_rate' không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Mặc định ước tính chi phí là 70% doanh thu đơn hàng
            total_cost = (total_revenue * Decimal('0.70')).quantize(Decimal('0.01'))

        total_profit = total_revenue - total_cost

        # 3. Tạo bản ghi báo cáo đơn hàng trong Database Transaction
        with transaction.atomic():
            order_report = OrderReport.objects.create(
                order_id=order_id,
                total_revenue=total_revenue,
                total_cost=total_cost,
                total_profit=total_profit
            )

            # 4. Tự động tạo ProductReport cho từng mặt hàng trong đơn hàng nếu có
            if auto_create_items and order_data.get('items'):
                for it in order_data['items']:
                    it_sold = it['quantity']
                    it_rev = it['total_price']
                    it_cost = (it_rev * Decimal('0.70')).quantize(Decimal('0.01'))
                    it_profit = it_rev - it_cost

                    ProductReport.objects.create(
                        order_report=order_report,
                        product_id=it['product_id'],
                        total_sold=it_sold,
                        revenue=it_rev,
                        cost=it_cost,
                        profit=it_profit
                    )

        serializer = OrderReportSerializer(order_report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderReportDetailDeleteAPIView(APIView):
    authentication_classes = [ExternalTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return OrderReport.objects.get(pk=pk)
        except OrderReport.DoesNotExist:
            return None

    # GET /reports/orders/<id>: Lấy chi tiết báo cáo cho một đơn hàng
    def get(self, request, pk):
        report = self.get_object(pk)
        if not report:
            return Response({"error": "Không tìm thấy báo cáo đơn hàng"}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # DELETE /reports/orders/<id>: Xóa báo cáo đơn hàng
    def delete(self, request, pk):
        report = self.get_object(pk)
        if not report:
            return Response({"error": "Không tìm thấy báo cáo đơn hàng"}, status=status.HTTP_404_NOT_FOUND)
        report.delete()
        return Response({"message": "Đã xóa báo cáo đơn hàng thành công"}, status=status.HTTP_204_NO_CONTENT)
