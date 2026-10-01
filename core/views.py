import base64
import jwt
import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .middleware import SECRET_KEY

# 1. API Đăng nhập & sinh JWT Token
@api_view(['POST'])
def login_view(request):
    username = request.data.get('userName')
    password_input = request.data.get('password')

    if not username or not password_input:
        return Response({'error': 'Vui lòng cung cấp userName và password'}, status=status.HTTP_400_BAD_REQUEST)

    # Giải mã Base64 từ client truyền lên (theo yêu cầu đề bài)
    try:
        decoded_password = base64.b64decode(password_input).decode('utf-8')
    except Exception:
        decoded_password = password_input  # Nếu client gửi text thường

    try:
        user = User.objects.get(UserName=username)
        
        # Kiểm tra mật khẩu (đơn giản hóa so sánh trực tiếp)
        if user.Password == decoded_password:
            # Tạo JWT Token (có hạn 1 giờ)
            payload = {
                'id_user': user.IdUser,
                'username': user.UserName,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

            # Lưu token vào DB
            user.Token = token
            user.save()

            return Response({'message': 'Đăng nhập thành công', 'token': token})
        else:
            return Response({'error': 'Mật khẩu không chính xác'}, status=status.HTTP_401_UNAUTHORIZED)
            
    except User.DoesNotExist:
        return Response({'error': 'Tài khoản không tồn tại'}, status=status.HTTP_404_NOT_FOUND)


# 2. API /auth kiểm tra tính hợp lệ của Token
@api_view(['POST'])
def verify_token_view(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Cần truyền token vào body'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return Response({'valid': True, 'data': payload})
    except jwt.ExpiredSignatureError:
        return Response({'valid': False, 'message': 'Token đã hết hạn'}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({'valid': False, 'message': 'Token không hợp lệ'}, status=status.HTTP_401_UNAUTHORIZED)


# 3. API protected "Hello World" (Được bảo vệ bởi Middleware)
@api_view(['GET'])
def hello_world_view(request):
    return Response({'message': 'Hello World! Bạn đã xác thực thành công.'})