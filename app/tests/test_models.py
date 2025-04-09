from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import Product, Cart, Paid, Log
from decimal import Decimal

class CustomUserModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user_data = {
            'username': 'testfarmer',
            'email': 'farmer@test.com',
            'password': 'testpass123',
            'role': 'farmer',
            'first_name': 'Test',
            'last_name': 'Farmer',
            'location': 'Test Location',
            'phone': '1234567890',
            'bank_name': 'Test Bank',
            'bank_number': '1234567890'
        }

    def test_create_user(self):
        user = self.User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.role, self.user_data['role'])
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

class ProductModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.farmer = self.User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123',
            role='farmer'
        )
        self.product_data = {
            'product_name': 'Test Product',
            'product_quantity': Decimal('10.00'),
            'product_price': Decimal('5.00'),
            'product_category': 'Vegetables',
            'farmer': self.farmer
        }

    def test_create_product(self):
        product = Product.objects.create(**self.product_data)
        self.assertEqual(product.product_name, self.product_data['product_name'])
        self.assertTrue(product.product_id.startswith('PRODUCT'))
        self.assertEqual(len(product.product_id), 13)  # PRODUCT + 6 digits

class CartModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.farmer = self.User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123',
            role='farmer'
        )
        self.buyer = self.User.objects.create_user(
            username='testbuyer',
            email='buyer@test.com',
            password='testpass123',
            role='buyer'
        )
        self.cart_data = {
            'order_name': 'Test Order',
            'order_quantity': Decimal('2.00'),
            'order_price': Decimal('5.00'),
            'order_category': 'Vegetables',
            'total_price': Decimal('10.00'),
            'farmer': self.farmer,
            'buyer': self.buyer
        }

    def test_create_cart(self):
        cart = Cart.objects.create(**self.cart_data)
        self.assertEqual(cart.order_name, self.cart_data['order_name'])
        self.assertEqual(cart.total_price, self.cart_data['total_price'])

class PaidModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.farmer = self.User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123',
            role='farmer'
        )
        self.buyer = self.User.objects.create_user(
            username='testbuyer',
            email='buyer@test.com',
            password='testpass123',
            role='buyer'
        )
        self.paid_data = {
            'paid_product_name': 'Test Product',
            'paid_product_quantity': Decimal('2.00'),
            'paid_product_price': Decimal('5.00'),
            'paid_product_category': 'Vegetables',
            'total_price': Decimal('10.00'),
            'transaction_reference': 'TEST123',
            'payment_status': 'pending',
            'farmer': self.farmer,
            'buyer': self.buyer
        }

    def test_create_paid(self):
        paid = Paid.objects.create(**self.paid_data)
        self.assertEqual(paid.paid_product_name, self.paid_data['paid_product_name'])
        self.assertEqual(paid.payment_status, 'pending')

class LogModelTest(TestCase):
    def test_create_log(self):
        log = Log.objects.create(
            message='Test log message',
            log_type='success'
        )
        self.assertEqual(log.message, 'Test log message')
        self.assertEqual(log.get_badge_color(), 'success')

    def test_log_badge_colors(self):
        log_types = {
            'success': 'success',
            'danger': 'danger',
            'warning': 'warning',
            'primary': 'primary',
            'info': 'info',
            'muted': 'muted',
            'unknown': 'primary'  # Default case
        }
        
        for log_type, expected_color in log_types.items():
            log = Log.objects.create(message=f'Test {log_type}', log_type=log_type)
            self.assertEqual(log.get_badge_color(), expected_color)
