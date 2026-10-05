import requests
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

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
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() not in ['bearer', 'token']:
            raise AuthenticationFailed('Header Authorization không đúng định dạng Bearer <token>.')

        token = parts[1]

        # 1. DÙNG 127.0.0.1 THAY VÌ localhost ĐỂ TRÁNH TIMEOUT TRÊN WINDOWS
        # 2. ĐÚNG PORT 8001 VÀ ENDPOINT /api/auth/ CỦA BÀI 2
        auth_url = 'http://127.0.0.1:8001/api/auth/'

        try:
            # Gửi đúng format {"token": token} theo yêu cầu của verify_token_view
            response = requests.post(
                auth_url,
                json={'token': token},
                timeout=3
            )
            
            if response.status_code != 200:
                raise AuthenticationFailed('Token không hợp lệ hoặc đã hết hạn.')

            result = response.json()
            if not result.get('valid'):
                raise AuthenticationFailed(result.get('message', 'Token không hợp lệ.'))

            user_payload = result.get('data', {})
            return (ServiceUser(user_payload), token)

        except requests.exceptions.RequestException:
            raise AuthenticationFailed('Không thể kết nối đến Auth Service.')