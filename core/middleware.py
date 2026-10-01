import jwt
from django.http import JsonResponse

SECRET_KEY = 'your-secret-key-here'  # Dùng chung khóa bảo mật để mã hóa/giải mã JWT

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Chỉ kiểm tra JWT với API protected (ví dụ: /hello/)
        if request.path == '/hello/':
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Thiếu Token hoặc Token không hợp lệ'}, status=401)

            token = auth_header.split(' ')[1]
            try:
                # Giải mã Token
                payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                request.user_id = payload.get('id_user')
            except jwt.ExpiredSignatureError:
                return JsonResponse({'error': 'Token đã hết hạn'}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({'error': 'Token không hợp lệ'}, status=401)

        return self.get_response(request)