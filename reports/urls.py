from django.urls import re_path
from .views import (
    ProductReportListCreateAPIView,
    ProductReportDetailDeleteAPIView,
    OrderReportListCreateAPIView,
    OrderReportDetailDeleteAPIView,
)

urlpatterns = [
    re_path(r'^reports/products/?$', ProductReportListCreateAPIView.as_view(), name='product-report-list-create'),
    re_path(r'^reports/products/(?P<pk>\d+)/?$', ProductReportDetailDeleteAPIView.as_view(), name='product-report-detail-delete'),
    re_path(r'^reports/orders/?$', OrderReportListCreateAPIView.as_view(), name='order-report-list-create'),
    re_path(r'^reports/orders/(?P<pk>\d+)/?$', OrderReportDetailDeleteAPIView.as_view(), name='order-report-detail-delete'),
]

