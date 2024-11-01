# serializers.py
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from rest_framework import serializers

from .models import Item, Order, OrderItem


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "price"]


class BaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "customer_name", "total_price", "address", "phone", "status"]


class OrderItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    order = BaseOrderSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), source="item", write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ["id", "item", "item_id", "order", "count"]

    def validate_count(self, count):
        if count <= 0:
            raise serializers.ValidationError(
                f"Count must be a positive integer. Received: {count}"
            )
        return count


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

    def update(self, instance, validated_data):
        order_items_data = validated_data.pop("order_items", None)
        instance.customer_name = validated_data.get(
            "customer_name", instance.customer_name
        )
        instance.phone = validated_data.get("phone", instance.phone)
        instance.address = validated_data.get("address", instance.address)

        if order_items_data is not None:
            instance.order_items.all().delete()
            total_price = 0
            for item_data in order_items_data:
                order_item = OrderItem.objects.create(order=instance, **item_data)
                total_price += order_item.item.price * order_item.count

            instance.total_price = total_price

        instance.save()
        return instance

    def validate_order_items(self, order_items):
        # Extract item IDs from the order_items list
        item_ids = [order_item["item"].id for order_item in order_items]

        # Fetch all items in one query with their remaining quantity
        items = (
            Item.objects.filter(id__in=item_ids)
            .annotate(
                consumed_count=Sum("order_items__count"),
                remaining_quantity=F("quantity") - Coalesce(F("consumed_count"), 0),
            )
            .values("id", "name", "quantity", "remaining_quantity")
        )

        items_dict = {item["id"]: item for item in items}
        # Validate the quantities for each order item. We could also move this part to
        # the `OrderItemSerializer`, but in that case the number of DB queries could be
        # high and lead to performance issues
        for order_item in order_items:
            item_id = order_item["item"].id
            requested_count = order_item["count"]

            if item_id not in items_dict:
                raise serializers.ValidationError(
                    f"Item with ID {item_id} does not exist."
                )

            item = items_dict[item_id]
            current_count = 0

            # if this is update, we should consider current count of this order as
            # remaining quantity
            if self.instance:
                try:
                    current_count = self.instance.order_items.get(
                        order_id=self.instance.id, item_id=item["id"]
                    ).count
                except OrderItem.DoesNotExist:
                    pass

            # raise error if we cannot satisfy the order count
            if item["remaining_quantity"] + current_count < requested_count:
                raise serializers.ValidationError(
                    f'Not enough stock for item {item["name"]}.'
                )

        return order_items
