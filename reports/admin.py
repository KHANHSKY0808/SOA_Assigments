from django.contrib import admin
from .models import OrderReport, ProductReport

class ProductReportInline(admin.TabularInline):
    model = ProductReport
    extra = 0

@admin.register(OrderReport)
class OrderReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_id', 'total_revenue', 'total_cost', 'total_profit', 'created_at')
    search_fields = ('order_id',)
    inlines = [ProductReportInline]

@admin.register(ProductReport)
class ProductReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_id', 'order_report', 'total_sold', 'revenue', 'cost', 'profit', 'created_at')
    search_fields = ('product_id',)
