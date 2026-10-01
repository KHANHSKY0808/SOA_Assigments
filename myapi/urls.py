"""
URL configuration for myapi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
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
]
