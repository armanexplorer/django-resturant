# serializers.py
from rest_framework import serializers

from .models import Item, Order, OrderItem


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "price"]


class OrderItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), source="item", write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ["id", "item", "item_id", "count"]


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_name",
            "phone",
            "address",
            "total_price",
            "status",
            "created_at",
            "order_items",
        ]
        # `total_price` will be calculated using request data, `created_at` will be
        # stored automatically, and `status` is better to be handled by API call
        # instead of direct overriding by the client
        read_only_fields = ["total_price", "created_at", "status"]

    def create(self, validated_data):
        order_items_data = validated_data.pop("order_items", [])
        order = Order.objects.create(**validated_data, status="new")

        # we should store the `total_price` because the price of item would be
        # changed in the future, and we cannot rely on instant DB queries to
        # calculate orders created in different datetime
        total_price = 0
        for item_data in order_items_data:
            order_item = OrderItem.objects.create(order=order, **item_data)
            total_price += order_item.item.price * order_item.count

        order.total_price = total_price
        order.save()
        return order
