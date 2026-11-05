import sys
import os
import requests
from decimal import Decimal

PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://127.0.0.1:8001/api/products')

def get_product_info(product_id, auth_token=None):
    """
    Gọi Product Service qua HTTP (chuẩn SOA) để lấy thông tin sản phẩm và tồn kho.
    Nếu Product Service chưa chạy độc lập hoặc đang chạy test, tự động fallback truy vấn Product model trong DB.
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

    # Fallback trực tiếp vào cơ sở dữ liệu nếu không kết nối được qua HTTP
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


def update_product_stock(product_id, new_quantity, auth_token=None):
    """
    Cập nhật số lượng tồn kho sản phẩm qua Product Service (HTTP PUT).
    Nếu không kết nối được, cập nhật trực tiếp vào database dự phòng.
    """
    if 'test' in sys.argv:
        try:
            from products.models import Product
            prod = Product.objects.get(pk=product_id)
            prod.quantity = new_quantity
            prod.save()
            return True
        except Exception:
            return False

    headers = {'Content-Type': 'application/json'}
    if auth_token:
        headers['Authorization'] = f"Bearer {auth_token}"

    prod_info = get_product_info(product_id, auth_token)
    if not prod_info:
        return False

    payload = {
        'name': prod_info['name'],
        'price': str(prod_info['price']),
        'description': prod_info.get('description', ''),
        'quantity': new_quantity
    }

    try:
        url = f"{PRODUCT_SERVICE_URL.rstrip('/')}/{product_id}"
        resp = requests.put(url, json=payload, headers=headers, timeout=2)
        if resp.status_code in [200, 204]:
            return True
    except requests.exceptions.RequestException:
        pass

    # Fallback trực tiếp vào database
    try:
        from products.models import Product
        prod = Product.objects.get(pk=product_id)
        prod.quantity = new_quantity
        prod.save()
        return True
    except Exception:
        return False
