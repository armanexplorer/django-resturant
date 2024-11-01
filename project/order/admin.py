from django.contrib import admin
from order.models import Item, Order, OrderItem

admin.site.register([Order, OrderItem, Item])
