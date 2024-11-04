from django.contrib import admin
from order.models import Item, Order, OrderItem

admin.site.register([Order, OrderItem, Item])

# TODO: we can define customized ModelAdmin for each of these model for better
#  monitoring on them
