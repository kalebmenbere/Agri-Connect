from django.contrib import admin
from .models import CustomUser, Product, Cart, Paid

admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CustomUser)
admin.site.register(Paid)