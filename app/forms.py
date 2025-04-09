from django import forms
from .models import  Product
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(help_text='A valid email address, please.', required=True)
    is_agreed = forms.BooleanField(required=True, label="I agree to the Terms of Service and Privacy Policy")

    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email', 'role', 'username', 'region', 'zone', 'phone', 'password1', 'password2', 'is_agreed']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'product_quantity', 'product_price', 'product_image', 'product_category']
