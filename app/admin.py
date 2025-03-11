from django.contrib import admin
from .models import CustomUser, Product, Cart, Request, Paid

admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Request)
admin.site.register(CustomUser)
admin.site.register(Paid)