from django.db import models

class OrderReport(models.Model):
    order_id = models.IntegerField(help_text="ID của đơn hàng (lưu vết để liên kết với dịch vụ quản lý đơn hàng)")
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, help_text="Tổng doanh thu của đơn hàng")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Tổng chi phí nhập sản phẩm trong đơn hàng")
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Tổng lợi nhuận (total_revenue - total_cost)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders_reports'

    def __str__(self):
        return f"OrderReport #{self.id} (Order #{self.order_id}): Revenue={self.total_revenue}, Profit={self.total_profit}"


class ProductReport(models.Model):
    order_report = models.ForeignKey(
        OrderReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_column='order_report_id',
        related_name='product_reports',
        help_text="ID đơn hàng (liên kết với bảng orders_reports)"
    )
    product_id = models.IntegerField(help_text="ID sản phẩm (lưu vết để liên kết với dịch vụ quản lý sản phẩm)")
    total_sold = models.IntegerField(help_text="Tổng số lượng sản phẩm đã bán")
    revenue = models.DecimalField(max_digits=10, decimal_places=2, help_text="Doanh thu từ sản phẩm")
    cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Chi phí nhập sản phẩm")
    profit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Lợi nhuận (revenue - cost)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_reports'

    def __str__(self):
        return f"ProductReport #{self.id} (Product #{self.product_id}): Sold={self.total_sold}, Profit={self.profit}"
