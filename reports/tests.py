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
from reports.models import OrderReport, ProductReport


class ReportServiceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Tạo user xác thực
        self.user = User.objects.create(
            UserName='reportuser',
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

        # Tạo dữ liệu mẫu Product
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

        # Tạo dữ liệu mẫu Order và OrderItems
        self.order = Order.objects.create(
            customer_name="Nguyen Van Test",
            customer_email="test@example.com",
            total_amount=Decimal('1700000.00'),
            status='completed'
        )
        self.item1 = OrderItem.objects.create(
            order=self.order,
            product_id=self.product1.id,
            product_name=self.product1.name,
            quantity=2,
            unit_price=self.product1.price,
            total_price=Decimal('1300000.00')
        )
        self.item2 = OrderItem.objects.create(
            order=self.order,
            product_id=self.product2.id,
            product_name=self.product2.name,
            quantity=1,
            unit_price=self.product2.price,
            total_price=Decimal('400000.00')
        )

    def test_unauthenticated_request_rejected(self):
        """Kiểm tra request không có token xác thực bị từ chối 401"""
        unauthed_client = APIClient()
        response = unauthed_client.get('/reports/orders')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response_prod = unauthed_client.get('/reports/products')
        self.assertEqual(response_prod.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_orders_report_success(self):
        """Kiểm tra POST /reports/orders tạo báo cáo đơn hàng và tự động tính toán doanh thu, chi phí, lợi nhuận"""
        payload = {
            "order_id": self.order.id,
            "total_cost": "1000000.00"
        }
        response = self.client.post('/reports/orders', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['order_id'], self.order.id)
        self.assertEqual(Decimal(str(response.data['total_revenue'])), Decimal('1700000.00'))
        self.assertEqual(Decimal(str(response.data['total_cost'])), Decimal('1000000.00'))
        # total_profit = 1700000 - 1000000 = 700000
        self.assertEqual(Decimal(str(response.data['total_profit'])), Decimal('700000.00'))

        # Kiểm tra tự động tạo ProductReport cho 2 mặt hàng trong đơn
        self.assertEqual(len(response.data['product_reports']), 2)

    def test_post_orders_report_default_cost_calculation(self):
        """Kiểm tra tạo báo cáo đơn hàng khi không truyền total_cost (ước tính 70% doanh thu)"""
        payload = {
            "order_id": self.order.id
        }
        response = self.client.post('/reports/orders', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_cost = (Decimal('1700000.00') * Decimal('0.70')).quantize(Decimal('0.01'))
        expected_profit = Decimal('1700000.00') - expected_cost
        self.assertEqual(Decimal(str(response.data['total_cost'])), expected_cost)
        self.assertEqual(Decimal(str(response.data['total_profit'])), expected_profit)

    def test_get_and_delete_orders_report(self):
        """Kiểm tra GET /reports/orders, GET /reports/orders/<id> và DELETE /reports/orders/<id>"""
        report = OrderReport.objects.create(
            order_id=self.order.id,
            total_revenue=Decimal('1700000.00'),
            total_cost=Decimal('1190000.00'),
            total_profit=Decimal('510000.00')
        )

        # GET list
        list_resp = self.client.get('/reports/orders')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(list_resp.data) >= 1)

        # GET detail
        detail_resp = self.client.get(f'/reports/orders/{report.id}')
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data['id'], report.id)

        # DELETE
        del_resp = self.client.delete(f'/reports/orders/{report.id}')
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OrderReport.objects.filter(id=report.id).exists())

    def test_post_products_report_aggregated(self):
        """Kiểm tra POST /reports/products tổng hợp dữ liệu từ Product Service & Order Service"""
        payload = {
            "product_id": self.product1.id,
            "cost_per_unit": "450000.00"
        }
        response = self.client.post('/reports/products', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['product_id'], self.product1.id)
        # item1 quantity = 2
        self.assertEqual(response.data['total_sold'], 2)
        # revenue = 1300000.00
        self.assertEqual(Decimal(str(response.data['revenue'])), Decimal('1300000.00'))
        # cost = 450000 * 2 = 900000
        self.assertEqual(Decimal(str(response.data['cost'])), Decimal('900000.00'))
        # profit = 1300000 - 900000 = 400000
        self.assertEqual(Decimal(str(response.data['profit'])), Decimal('400000.00'))

    def test_post_products_report_with_order_report(self):
        """Kiểm tra POST /reports/products liên kết với một OrderReport cụ thể"""
        order_rep = OrderReport.objects.create(
            order_id=self.order.id,
            total_revenue=Decimal('1700000.00'),
            total_cost=Decimal('1000000.00'),
            total_profit=Decimal('700000.00')
        )

        payload = {
            "order_report_id": order_rep.id,
            "product_id": self.product2.id,
            "cost": "250000.00"
        }
        response = self.client.post('/reports/products', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['order_report_id'], order_rep.id)
        self.assertEqual(response.data['product_id'], self.product2.id)
        self.assertEqual(response.data['total_sold'], 1)
        self.assertEqual(Decimal(str(response.data['revenue'])), Decimal('400000.00'))
        self.assertEqual(Decimal(str(response.data['cost'])), Decimal('250000.00'))
        # profit = 400000 - 250000 = 150000
        self.assertEqual(Decimal(str(response.data['profit'])), Decimal('150000.00'))

    def test_get_and_delete_products_report(self):
        """Kiểm tra GET /reports/products, GET /reports/products/<id> và DELETE /reports/products/<id>"""
        prod_rep = ProductReport.objects.create(
            product_id=self.product1.id,
            total_sold=5,
            revenue=Decimal('3250000.00'),
            cost=Decimal('2275000.00'),
            profit=Decimal('975000.00')
        )

        # GET list
        list_resp = self.client.get('/reports/products')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(list_resp.data) >= 1)

        # GET detail
        detail_resp = self.client.get(f'/reports/products/{prod_rep.id}')
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data['id'], prod_rep.id)

        # DELETE
        del_resp = self.client.delete(f'/reports/products/{prod_rep.id}')
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProductReport.objects.filter(id=prod_rep.id).exists())
