from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from dj4e import settings




class CustomUser(AbstractUser):
    STATUS = (
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    )

    REGIONS = (
        ('Addis Ababa', 'Addis Ababa'),
        ('Afar', 'Afar'),
        ('Amhara', 'Amhara'),
        ('Benishangul-Gumuz', 'Benishangul-Gumuz'),
        ('Dire Dawa', 'Dire Dawa'),
        ('Gambela', 'Gambela'),
        ('Harari', 'Harari'),
        ('Oromia', 'Oromia'),
        ('Sidama', 'Sidama'),
        ('SNNP', 'SNNP'),
        ('Somali', 'Somali'),
        ('Tigray', 'Tigray'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField("Role", max_length=100, choices=STATUS, default='none', blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    region = models.CharField(max_length=100, choices=REGIONS)
    zone = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    is_activated = models.BooleanField(default=False)
    is_agreed = models.BooleanField(default=True)
    
    def __str__(self):
        return self.username

User = get_user_model()

class Product(models.Model):
    product_id = models.CharField(max_length=255, unique=True, editable=False)  # New field for custom product ID
    product_name = models.CharField(max_length=200)
    product_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_image = models.ImageField(upload_to='products/', null=True, blank=True)
    product_category =models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='farmer_product', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'farmer'}
    )
    def __str__(self):
        return f"Products {self.id} - {self.product_name}"

class Cart(models.Model):
    product_id = models.CharField(max_length=255, unique=False, editable=False, default="PRODUCT")  # New field for custom product ID
    order_name = models.CharField(max_length=200)
    order_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_image = models.ImageField(upload_to='products/', null=True, blank=True)
    order_category =models.CharField(max_length=20)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField()
    ordered_at = models.DateTimeField(auto_now_add=True)
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='farmer_order', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'farmer'}
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='buyer_order', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'buyer'}
    )
    def __str__(self):
        return f"Orders {self.id}"


class Paid(models.Model):
    product_id = models.CharField(max_length=255, unique=False, editable=False, default="PRODUCT")  # New field for custom product ID
    paid_product_name = models.CharField(max_length=200)
    paid_product_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_product_image = models.ImageField(upload_to='products/', null=True, blank=True)
    paid_product_category = models.CharField(max_length=20)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField()
    ordered_at = models.DateTimeField()
    paid_at = models.DateTimeField()
    # Add transaction reference and status for tracking
    transaction_reference = models.CharField(max_length=200, unique=True)  # Reference for the transaction
    payment_status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')], default='pending')  # Payment status
    
    # Foreign Keys to link the farmer and buyer
    farmer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='farmer_paid_product', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'farmer'}
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='buyer_paid_product', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'buyer'}
    )
    

    def __str__(self):
        return f"Paid Product {self.id} for Buyer {self.buyer}"



# app/models.py

from django.db import models
from django.contrib.auth.models import User

class UserActivityLog(models.Model):
    ACTION_CHOICES = [
        ('logged_in', 'Logged In'),
        ('logged_out', 'Logged Out'),
        ('registered', 'Registered'),
        ('viewed_product', 'Viewed Product'),
        ('ordered_product', 'Ordered Product'),
        ('edited_profile', 'Edited Profile'),
        ('searched', 'Searched'),
        ('added_to_cart', 'Added to Cart'),
        ('removed_from_cart', 'Removed from Cart'),
        ('checked_out', 'Checked Out'),
        ('updated_password', 'Updated Password'),
        ('product_added', 'Product Added'),
        ('failed_login', 'Failed Login'),
        ('failed_checkout', 'Failed Checkout'),
        ('failed_registration', 'Failed Registration'),
        ('failed_password_update', 'Failed Password Update'),

    ]

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    description = models.TextField(blank=True, default="Description not provided")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} ({self.status}) @ {self.timestamp}"


class Log(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    log_type = models.CharField(max_length=50, default="info")

    def get_badge_color(self):
        if self.log_type == "success":
            return "success"
        elif self.log_type == "danger":
            return "danger"
        elif self.log_type == "warning":
            return "warning"
        elif self.log_type == "primary":
            return "primary"
        elif self.log_type == "info":
            return "info"
        elif self.log_type == "muted":
            return "muted"
        else:
            return "primary"

    def __str__(self):
        return f"{self.timestamp} - {self.message}"
