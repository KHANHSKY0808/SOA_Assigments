from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(),
        source='order',
        required=False
    )

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'order_id',
            'product_id',
            'product_name',
            'quantity',
            'unit_price',
            'total_price',
        ]
        read_only_fields = ['id', 'total_price']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'customer_name',
            'customer_email',
            'total_amount',
            'status',
            'created_at',
            'updated_at',
            'items',
        ]
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']

