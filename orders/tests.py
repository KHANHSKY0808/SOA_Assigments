import jwt
import datetime
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from core.models import User
from core.middleware import SECRET_KEY
from products.models import Product
from orders.models import Order, OrderItem


class OrderServiceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Tạo user xác thực
        self.user = User.objects.create(
            UserName='testuser',
            Password='password123'
        )

        # Tạo JWT token hợp lệ
        payload = {
            'id_user': self.user.IdUser,
            'username': self.user.UserName,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        self.token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Tạo sản phẩm mẫu có sẵn tồn kho
        self.product1 = Product.objects.create(
            name='Bàn phím cơ DareU',
            description='Bàn phím cơ chơi game',
            price=Decimal('650000.00'),
            quantity=10
        )
        self.product2 = Product.objects.create(
            name='Chuột Logitech G102',
            description='Chuột gaming',
            price=Decimal('400000.00'),
            quantity=5
        )

    def test_unauthenticated_request_rejected(self):
        """Kiểm tra request không có token xác thực bị từ chối 401"""
        unauthed_client = APIClient()
        response = unauthed_client.get('/orders')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_orders_success_and_inventory_deduction(self):
        """Kiểm tra tạo đơn hàng thành công và tự động trừ tồn kho"""
        payload = {
            "customer_name": "Nguyen Van A",
            "customer_email": "vana@example.com",
            "items": [
                {
                    "product_id": self.product1.id,
                    "quantity": 2
                },
                {
                    "product_id": self.product2.id,
                    "quantity": 1
                }
            ]
        }
        response = self.client.post('/orders', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer_name'], "Nguyen Van A")
        self.assertEqual(response.data['status'], "pending")

        # Tổng tiền: 2 * 650000 + 1 * 400000 = 1700000
        expected_total = Decimal('1700000.00')
        self.assertEqual(Decimal(str(response.data['total_amount'])), expected_total)
        self.assertEqual(len(response.data['items']), 2)

        # Kiểm tra tồn kho sau khi trừ
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        self.assertEqual(self.product1.quantity, 8)  # 10 - 2
        self.assertEqual(self.product2.quantity, 4)  # 5 - 1

    def test_post_orders_out_of_stock_rejected(self):
        """Kiểm tra tạo đơn hàng bị từ chối nếu số lượng vượt quá tồn kho"""
        payload = {
            "customer_name": "Nguyen Van B",
            "customer_email": "vanb@example.com",
            "items": [
                {
                    "product_id": self.product2.id,
                    "quantity": 99  # Hiện chỉ có 5
                }
            ]
        }
        response = self.client.post('/orders', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("không đủ tồn kho", response.data['error'])

        # Tồn kho không bị thay đổi
        self.product2.refresh_from_db()
        self.assertEqual(self.product2.quantity, 5)

    def test_get_orders_list_and_detail(self):
        """Kiểm tra GET /orders và GET /orders/<id>"""
        order = Order.objects.create(
            customer_name="Tran Thi C",
            customer_email="thic@example.com",
            total_amount=Decimal('650000.00'),
            status='pending'
        )
        OrderItem.objects.create(
            order=order,
            product_id=self.product1.id,
            product_name=self.product1.name,
            quantity=1,
            unit_price=self.product1.price,
            total_price=self.product1.price
        )

        # GET /orders
        list_resp = self.client.get('/orders')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(list_resp.data) >= 1)

        # GET /orders/<id>
        detail_resp = self.client.get(f'/orders/{order.id}')
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data['customer_name'], "Tran Thi C")
        self.assertEqual(len(detail_resp.data['items']), 1)

    def test_put_orders_status_update_and_cancel_restock(self):
        """Kiểm tra cập nhật trạng thái đơn hàng và hoàn trả tồn kho khi hủy đơn"""
        # Tạo đơn hàng và trừ 3 sản phẩm product1
        order = Order.objects.create(
            customer_name="Le Van D",
            customer_email="vand@example.com",
            total_amount=Decimal('1950000.00'),
            status='pending'
        )
        OrderItem.objects.create(
            order=order,
            product_id=self.product1.id,
            product_name=self.product1.name,
            quantity=3,
            unit_price=self.product1.price,
            total_price=Decimal('1950000.00')
        )
        self.product1.quantity = 7  # Đã bị trừ 3
        self.product1.save()

        # Cập nhật sang completed
        put_resp = self.client.put(f'/orders/{order.id}', {'status': 'completed'}, format='json')
        self.assertEqual(put_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(put_resp.data['status'], 'completed')

        # Cập nhật sang cancelled -> hoàn trả tồn kho
        cancel_resp = self.client.put(f'/orders/{order.id}', {'status': 'cancelled'}, format='json')
        self.assertEqual(cancel_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel_resp.data['status'], 'cancelled')

        self.product1.refresh_from_db()
        self.assertEqual(self.product1.quantity, 10)  # Hoàn trả lại 3 sản phẩm (7 + 3 = 10)

    def test_delete_orders_and_restock(self):
        """Kiểm tra xóa đơn hàng và hoàn trả kho nếu chưa hủy"""
        order = Order.objects.create(
            customer_name="Pham E",
            customer_email="phame@example.com",
            total_amount=Decimal('650000.00'),
            status='pending'
        )
        OrderItem.objects.create(
            order=order,
            product_id=self.product1.id,
            product_name=self.product1.name,
            quantity=2,
            unit_price=self.product1.price,
            total_price=Decimal('1300000.00')
        )
        self.product1.quantity = 8
        self.product1.save()

        del_resp = self.client.delete(f'/orders/{order.id}')
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Order.objects.filter(id=order.id).exists())
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.quantity, 10)  # 8 + 2

    def test_order_items_crud_operations(self):
        """Kiểm tra toàn bộ CRUD chi tiết đơn hàng (/order_items)"""
        order = Order.objects.create(
            customer_name="Khach Hang Test",
            customer_email="khach@example.com",
            total_amount=Decimal('0.00'),
            status='pending'
        )

        # 1. POST /order_items: Thêm mặt hàng mới
        post_data = {
            "order_id": order.id,
            "product_id": self.product1.id,
            "quantity": 2
        }
        post_resp = self.client.post('/order_items', post_data, format='json')
        self.assertEqual(post_resp.status_code, status.HTTP_201_CREATED)
        item_id = post_resp.data['id']
        self.assertEqual(Decimal(str(post_resp.data['total_price'])), Decimal('1300000.00'))

        # Kiểm tra tồn kho và tổng tiền order
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.quantity, 8)  # 10 - 2
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal('1300000.00'))

        # 2. GET /order_items?order_id=...
        list_resp = self.client.get(f'/order_items?order_id={order.id}')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data), 1)

        # 3. GET /order_items/<id>
        detail_resp = self.client.get(f'/order_items/{item_id}')
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data['product_name'], self.product1.name)

        # 4. PUT /order_items/<id>: Tăng số lượng từ 2 lên 4 (cần thêm 2 cái từ kho)
        put_resp = self.client.put(f'/order_items/{item_id}', {'quantity': 4}, format='json')
        self.assertEqual(put_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(put_resp.data['quantity'], 4)
        self.assertEqual(Decimal(str(put_resp.data['total_price'])), Decimal('2600000.00'))

        self.product1.refresh_from_db()
        self.assertEqual(self.product1.quantity, 6)  # 8 - 2 = 6
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal('2600000.00'))

        # 5. DELETE /order_items/<id>: Xóa mặt hàng -> hoàn lại 4 sản phẩm vào kho
        del_resp = self.client.delete(f'/order_items/{item_id}')
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)

        self.product1.refresh_from_db()
        self.assertEqual(self.product1.quantity, 10)  # 6 + 4 = 10
        order.refresh_from_db()
        self.assertEqual(order.total_amount, Decimal('0.00'))
