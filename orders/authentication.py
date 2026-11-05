import sys
import os
import requests
import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from core.middleware import SECRET_KEY

class ServiceUser:
    """Đối tượng giả lập user hợp lệ để DRF cho phép qua permission IsAuthenticated"""
    def __init__(self, data):
        self.data = data
        self.username = data.get('username')
        self.id = data.get('id_user')
        self.is_authenticated = True

    def __str__(self):
        return str(self.username)

class ExternalTokenAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return 'Bearer'

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() not in ['bearer', 'token']:
            raise AuthenticationFailed('Header Authorization không đúng định dạng Bearer <token>.')

        token = parts[1]

        # 1. Khi chạy kiểm thử (Django test), decode trực tiếp để chạy nhanh và độc lập
        if 'test' in sys.argv:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                return (ServiceUser(payload), token)
            except jwt.ExpiredSignatureError:
                raise AuthenticationFailed('Token đã hết hạn.')
            except jwt.InvalidTokenError:
                raise AuthenticationFailed('Token không hợp lệ.')

        # 2. Khi chạy thực tế: gọi Auth Service qua HTTP theo chuẩn kiến trúc SOA
        auth_url = os.environ.get('AUTH_SERVICE_URL', 'http://127.0.0.1:8001/api/auth/')
        try:
            response = requests.post(
                auth_url,
                json={'token': token},
                timeout=2
            )
            if response.status_code == 200:
                result = response.json()
                if result.get('valid'):
                    user_payload = result.get('data', {})
                    return (ServiceUser(user_payload), token)
                else:
                    raise AuthenticationFailed(result.get('message', 'Token không hợp lệ.'))
            elif response.status_code == 401:
                result = response.json()
                raise AuthenticationFailed(result.get('message', 'Token không hợp lệ hoặc đã hết hạn.'))
        except requests.exceptions.RequestException:
            # Fallback nếu Auth Service chưa bật riêng port (hỗ trợ kiểm thử cùng server)
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                return (ServiceUser(payload), token)
            except Exception:
                raise AuthenticationFailed('Không thể kết nối đến Auth Service.')
