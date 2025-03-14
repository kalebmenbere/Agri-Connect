from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Product, Cart, Paid, Log
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile

class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        
        # Create test users
        self.farmer = self.User.objects.create_user(
            username='testfarmer',
            email='farmer@test.com',
            password='testpass123',
            role='farmer',
            is_active=True
        )
        
        self.buyer = self.User.objects.create_user(
            username='testbuyer',
            email='buyer@test.com',
            password='testpass123',
            role='buyer',
            is_active=True
        )

        # Create a test product
        self.product = Product.objects.create(
            product_name='Test Product',
            product_quantity=Decimal('10.00'),
            product_price=Decimal('5.00'),
            product_category='Vegetables',
            farmer=self.farmer
        )

class LoginViewTest(ViewTestCase):
    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'testfarmer',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('product_list'))

    def test_login_failure(self):
        response = self.client.post(reverse('login'), {
            'username': 'testfarmer',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

class ProductViewsTest(ViewTestCase):
    def test_product_list_view(self):
        self.client.login(username='testbuyer', password='testpass123')
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product/product_list.html')
        self.assertContains(response, 'Test Product')

    def test_add_product_view_farmer(self):
        self.client.login(username='testfarmer', password='testpass123')
        
        # Test GET request
        response = self.client.get(reverse('add_product'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'farmer/add_product.html')

        # Test POST request
        image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post(reverse('add_product'), {
            'product_name': 'New Product',
            'product_quantity': '5.00',
            'product_price': '10.00',
            'product_category': 'Fruits',
            'product_image': image
        })
        self.assertRedirects(response, reverse('product_list'))
        self.assertTrue(Product.objects.filter(product_name='New Product').exists())

    def test_add_product_view_buyer(self):
        # Buyers should not be able to add products
        self.client.login(username='testbuyer', password='testpass123')
        response = self.client.get(reverse('add_product'))
        self.assertRedirects(response, reverse('product_list'))

class CartViewsTest(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.cart = Cart.objects.create(
            order_name='Test Order',
            order_quantity=Decimal('2.00'),
            order_price=Decimal('5.00'),
            order_category='Vegetables',
            total_price=Decimal('10.00'),
            farmer=self.farmer,
            buyer=self.buyer
        )

    def test_cart_view(self):
        self.client.login(username='testbuyer', password='testpass123')
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart/cart.html')
        self.assertContains(response, 'Test Order')

    def test_add_to_cart(self):
        self.client.login(username='testbuyer', password='testpass123')
        response = self.client.post(reverse('add_to_cart'), {
            'product_id': self.product.id,
            'quantity': '1'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cart.objects.filter(order_name='Test Product').exists())

class PaymentViewsTest(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.paid = Paid.objects.create(
            paid_product_name='Test Product',
            paid_product_quantity=Decimal('2.00'),
            paid_product_price=Decimal('5.00'),
            paid_product_category='Vegetables',
            total_price=Decimal('10.00'),
            transaction_reference='TEST123',
            payment_status='pending',
            farmer=self.farmer,
            buyer=self.buyer
        )

    def test_payment_detail_view(self):
        self.client.login(username='testbuyer', password='testpass123')
        response = self.client.get(reverse('payment_detail', args=[self.paid.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/payment_detail.html')

    def test_paid_list_view(self):
        self.client.login(username='testbuyer', password='testpass123')
        response = self.client.get(reverse('paid'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payment/paid.html')

class AdminViewsTest(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='adminpass123'
        )

    def test_admin_dashboard(self):
        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/dashboard.html')

    def test_farmer_list(self):
        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.get(reverse('farmer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/farmer_list.html')
        self.assertContains(response, 'testfarmer')

    def test_buyer_list(self):
        self.client.login(username='testadmin', password='adminpass123')
        response = self.client.get(reverse('buyer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/buyer_list.html')
        self.assertContains(response, 'testbuyer')
