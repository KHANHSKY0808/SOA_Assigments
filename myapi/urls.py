"""
URL configuration for myapi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from core.views import login_view, verify_token_view, hello_world_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view),         # URL Đăng nhập
    path('auth/', verify_token_view),   # URL Xác thực token localhost:8000/auth
    path('hello/', hello_world_view),   # API Hello World sử dụng Middleware
    path('api/', include('core.urls')),
    path('', include('orders.urls')),   # Dịch vụ Quản lý Đơn hàng (Orders & Order Items)
    path('', include('products.urls')), # Dịch vụ Quản lý Sản phẩm (Products)
    path('', include('reports.urls')),  # Dịch vụ Báo cáo (Reports Service)
]
