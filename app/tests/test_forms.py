from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from app.forms import UserRegistrationForm, ProductForm
from django.contrib.auth import get_user_model

class UserRegistrationFormTest(TestCase):
    def test_valid_registration_form(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'farmer',
            'first_name': 'Test',
            'last_name': 'User',
            'location': 'Test Location',
            'phone': '1234567890',
            'bank_name': 'Test Bank',
            'bank_number': '1234567890'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'wrongpass123',
            'role': 'farmer',
            'first_name': 'Test',
            'last_name': 'User',
            'location': 'Test Location',
            'phone': '1234567890',
            'bank_name': 'Test Bank',
            'bank_number': '1234567890'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_duplicate_email(self):
        User = get_user_model()
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='testpass123'
        )
        
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',  # Duplicate email
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'farmer',
            'first_name': 'Test',
            'last_name': 'User',
            'location': 'Test Location',
            'phone': '1234567890',
            'bank_name': 'Test Bank',
            'bank_number': '1234567890'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

class ProductFormTest(TestCase):
    def setUp(self):
        self.image = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )

    def test_valid_product_form(self):
        form_data = {
            'product_name': 'Test Product',
            'product_quantity': '10.00',
            'product_price': '5.00',
            'product_category': 'Vegetables',
        }
        form_files = {'product_image': self.image}
        form = ProductForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())

    def test_invalid_product_form(self):
        # Test with negative price
        form_data = {
            'product_name': 'Test Product',
            'product_quantity': '-10.00',  # Invalid negative quantity
            'product_price': '5.00',
            'product_category': 'Vegetables',
        }
        form_files = {'product_image': self.image}
        form = ProductForm(data=form_data, files=form_files)
        self.assertFalse(form.is_valid())
        self.assertIn('product_quantity', form.errors)

    def test_missing_required_fields(self):
        form_data = {
            'product_name': '',  # Missing required field
            'product_quantity': '10.00',
            'product_price': '5.00',
            'product_category': 'Vegetables',
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('product_name', form.errors)
