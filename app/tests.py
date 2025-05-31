from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import Product, Log
from app.forms import ProductForm

class AddProductViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a farmer user
        self.farmer_user = User.objects.create_user(username='farmer1', password='pass123')
        self.farmer_user.role = 'farmer'
        self.farmer_user.save()

        # Create a non-farmer user
        self.non_farmer_user = User.objects.create_user(username='buyer1', password='pass123')
        self.non_farmer_user.role = 'buyer'
        self.non_farmer_user.save()

        self.url = reverse('add_product')  # Make sure the URL name matches your urls.py

    def test_non_farmer_cannot_add_product(self):
        self.client.login(username='buyer1', password='pass123')
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('product_list'))
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Not Autorized" in str(m) for m in messages))

    def test_get_request_returns_form(self):
        self.client.login(username='farmer1', password='pass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], ProductForm)

    def test_valid_post_creates_product(self):
        self.client.login(username='farmer1', password='pass123')

        # Example valid data - adjust fields according to your ProductForm
        data = {
            'product_name': 'Test Product',
            'price': 100,
            # Add other required form fields here
        }

        response = self.client.post(self.url, data, follow=True)
        
        self.assertRedirects(response, reverse('product_list'))
        self.assertTrue(Product.objects.filter(product_name='Test Product', farmer=self.farmer_user).exists())

        # Check success message
        messages = list(response.context['messages'])
        self.assertTrue(any("Product created successfully" in str(m) for m in messages))

        # Check that log is created
        self.assertTrue(Log.objects.filter(message__contains='added product').exists())

    def test_invalid_post_shows_errors(self):
        self.client.login(username='farmer1', password='pass123')

        # Missing required fields to cause form invalidation
        data = {
            'product_name': '',  # empty name should fail validation
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'product_name', 'This field is required.')
