from django.contrib import admin
from .models import Product, Order, OrderItem
from .models import Product, Order, OrderItem, Review

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Review)