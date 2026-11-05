from django.urls import path, re_path
from .views import (
    OrderListCreateAPIView,
    OrderDetailAPIView,
    OrderItemListCreateAPIView,
    OrderItemDetailAPIView
)

urlpatterns = [
    re_path(r'^orders/?$', OrderListCreateAPIView.as_view(), name='order-list-create'),
    re_path(r'^orders/(?P<pk>\d+)/?$', OrderDetailAPIView.as_view(), name='order-detail'),
    re_path(r'^order_items/?$', OrderItemListCreateAPIView.as_view(), name='order-item-list-create'),
    re_path(r'^order_items/(?P<pk>\d+)/?$', OrderItemDetailAPIView.as_view(), name='order-item-detail'),
]

