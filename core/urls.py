from django.urls import path
from .views import login_view, verify_token_view, hello_world_view

urlpatterns = [
    path('login/', login_view),
    path('auth/', verify_token_view),
    path('hello/', hello_world_view),
]