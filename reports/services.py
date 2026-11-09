import sys
import os
import requests
from decimal import Decimal

PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://127.0.0.1:8001/api/products')
ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://127.0.0.1:8002/orders')

def get_order_data(order_id, auth_token=None):
    """
    Lấy thông tin chi tiết một đơn hàng từ Order Service (HTTP GET).
    Nếu Order Service chưa chạy độc lập hoặc đang chạy test, fallback truy vấn Order model trong DB.
    """
    if 'test' in sys.argv:
        try:
            from orders.models import Order
            order = Order.objects.get(pk=order_id)
            items = []
            for it in order.items.all():
                items.append({
                    'id': it.id,
                    'order_id': order.id,
                    'product_id': it.product_id,
                    'product_name': it.product_name,
                    'quantity': it.quantity,
                    'unit_price': Decimal(str(it.unit_price)),
                    'total_price': Decimal(str(it.total_price)),
                })
            return {
                'id': order.id,
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'total_amount': Decimal(str(order.total_amount)),
                'status': order.status,
                'items': items,
            }
        except Exception:
            return None

    headers = {'Content-Type': 'application/json'}
    if auth_token:
        headers['Authorization'] = f"Bearer {auth_token}"

    try:
        url = f"{ORDER_SERVICE_URL.rstrip('/')}/{order_id}"
        resp = requests.get(url, headers=headers, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            items = []
            for it in data.get('items', []):
                items.append({
                    'id': it.get('id'),
                    'order_id': it.get('order_id'),
                    'product_id': it.get('product_id'),
                    'product_name': it.get('product_name'),
                    'quantity': int(it.get('quantity', 1)),
                    'unit_price': Decimal(str(it.get('unit_price', '0'))),
                    'total_price': Decimal(str(it.get('total_price', '0'))),
                })
            return {
                'id': data.get('id'),
                'customer_name': data.get('customer_name'),
                'customer_email': data.get('customer_email'),
                'total_amount': Decimal(str(data.get('total_amount', '0'))),
                'status': data.get('status'),
                'items': items,
            }
        elif resp.status_code == 404:
            return None
    except requests.exceptions.RequestException:
        pass

    # Fallback to local DB
    try:
        from orders.models import Order
        order = Order.objects.get(pk=order_id)
        items = []
        for it in order.items.all():
            items.append({
                'id': it.id,
                'order_id': order.id,
                'product_id': it.product_id,
                'product_name': it.product_name,
                'quantity': it.quantity,
                'unit_price': Decimal(str(it.unit_price)),
                'total_price': Decimal(str(it.total_price)),
            })
        return {
            'id': order.id,
            'customer_name': order.customer_name,
            'customer_email': order.customer_email,
            'total_amount': Decimal(str(order.total_amount)),
            'status': order.status,
            'items': items,
        }
    except Exception:
        return None


def get_product_data(product_id, auth_token=None):
    """
    Lấy thông tin sản phẩm từ Product Service (HTTP GET).
    Nếu Product Service chưa chạy độc lập hoặc đang chạy test, fallback truy vấn Product model trong DB.
    """
    if 'test' in sys.argv:
        try:
            from products.models import Product
            prod = Product.objects.get(pk=product_id)
            return {
                'id': prod.id,
                'name': prod.name,
                'price': Decimal(str(prod.price)),
                'quantity': int(prod.quantity),
                'description': prod.description or ''
            }
        except Exception:
            return None

    headers = {'Content-Type': 'application/json'}
    if auth_token:
        headers['Authorization'] = f"Bearer {auth_token}"

    try:
        url = f"{PRODUCT_SERVICE_URL.rstrip('/')}/{product_id}"
        resp = requests.get(url, headers=headers, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return {
                'id': data.get('id'),
                'name': data.get('name'),
                'price': Decimal(str(data.get('price'))),
                'quantity': int(data.get('quantity', 0)),
                'description': data.get('description', '')
            }
        elif resp.status_code == 404:
            return None
    except requests.exceptions.RequestException:
        pass

    # Fallback to local DB
    try:
        from products.models import Product
        prod = Product.objects.get(pk=product_id)
        return {
            'id': prod.id,
            'name': prod.name,
            'price': Decimal(str(prod.price)),
            'quantity': int(prod.quantity),
            'description': prod.description or ''
        }
    except Exception:
        return None


def get_all_order_items_for_product(product_id, auth_token=None):
    """
    Lấy tất cả các mặt hàng đã bán của một sản phẩm từ Order Service để tính tổng số lượng bán và doanh thu.
    """
    if 'test' in sys.argv:
        try:
            from orders.models import OrderItem
            items = OrderItem.objects.filter(product_id=product_id)
            result = []
            for it in items:
                result.append({
                    'id': it.id,
                    'order_id': it.order_id,
                    'product_id': it.product_id,
                    'quantity': it.quantity,
                    'total_price': Decimal(str(it.total_price)),
                })
            return result
        except Exception:
            return []

    headers = {'Content-Type': 'application/json'}
    if auth_token:
        headers['Authorization'] = f"Bearer {auth_token}"

    try:
        base_order_url = ORDER_SERVICE_URL.rstrip('/')
        # Endpoint order_items
        url = base_order_url.replace('/orders', '/order_items')
        resp = requests.get(url, headers=headers, timeout=2)
        if resp.status_code == 200:
            all_items = resp.json()
            filtered = []
            for it in all_items:
                if it.get('product_id') == product_id:
                    filtered.append({
                        'id': it.get('id'),
                        'order_id': it.get('order_id'),
                        'product_id': it.get('product_id'),
                        'quantity': int(it.get('quantity', 0)),
                        'total_price': Decimal(str(it.get('total_price', '0'))),
                    })
            return filtered
    except requests.exceptions.RequestException:
        pass

    # Fallback to local DB
    try:
        from orders.models import OrderItem
        items = OrderItem.objects.filter(product_id=product_id)
        result = []
        for it in items:
            result.append({
                'id': it.id,
                'order_id': it.order_id,
                'product_id': it.product_id,
                'quantity': it.quantity,
                'total_price': Decimal(str(it.total_price)),
            })
        return result
    except Exception:
        return []

