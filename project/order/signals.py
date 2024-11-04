# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order


@receiver(post_save, sender=Order)
def notify_order_total_price(sender, instance, created, **kwargs):
    if instance.total_price and instance.total_price > 50:
        print(f"SMS sent to {instance.phone}")
