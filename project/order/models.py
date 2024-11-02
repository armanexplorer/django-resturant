from django.db import models
from django.core.validators import MinValueValidator


class Order(models.Model):
    status_choices = [
        ("new", "New"),
        ("preparing", "Preparing"),
        ("ready", "Ready"),
        ("delivered", "Delivered"),
        ("canceled", "Canceled"),
    ]
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    # to create the order first and then relate it to its OrderItems,
    # `total_price` should be nullable
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=status_choices, default="new")
    created_at = models.DateTimeField(auto_now_add=True)


class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="order_items")
    count = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
