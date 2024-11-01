# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order

# from .utils import update_inventory


@receiver(post_save, sender=Order)
def notify_order_total_price(sender, instance, created, **kwargs):
    if instance.total_price and instance.total_price > 50:
        print(f"SMS sent to {instance.phone}")


# @receiver(post_save, sender=Order)
# def update_inventory_after_order_delivery(sender, instance, created, **kwargs):
#     if instance.status == 'delivered':
#         for order_item in instance.order_items.all():
#             update_inventory(order_item.name, order_item.count)
