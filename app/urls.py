from django.views.generic import TemplateView
from django.urls import path
from .views import  register,admin_login,admin_dashboard, farmer_list, users_profile,buyer_list
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('contact/', views.contact_view, name='contact'),
    path('admin_contact/', views.admin_contact_view, name='admin_contact'),

    path('', views.home_view, name='home'),
    path('login/', views.custom_login, name='login'),
    path('policy/', views.policy, name='policy'),
    path('logout/', views.custom_logout, name='logout'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/product_detail/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/product_detail/add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/chapa_callback/<int:item_id>/', views.chapa_callback, name='chapa_callback'),
    path('cart/chapa_return/', views.chapa_return, name='chapa_return'),
    path('cart/payment_detail/<int:item_id>/', views.payment_detail, name='payment_detail'),
    path("cart/delete_cart_items/", views.delete_cart_items, name="delete_cart_items"),
    path("cartupdate_cart/<int:cart_id>/", views.update_cart, name="update_cart"),
    path('paid/', views.paid, name='paid'),
    path('cart/paid_detail/<int:item_id>/', views.paid_detail, name='paid_detail'),

    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    path('dashboard/product/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('dashboard/paid/edit/<int:paid_id>/', views.edit_paid, name='edit_paid'),
    path('dashboard/cart/edit/<int:cart_id>/', views.edit_cart, name='edit_cart'),
    path('product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('cart/<int:cart_id>/delete/', views.delete_cart, name='delete_cart'), 
    path('paid/<int:paid_id>/delete/', views.delete_paid, name='delete_paid'),

    path("admin-login/", admin_login, name="admin_login"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/farmer-list/", farmer_list, name="farmer_list"),
    path("admin-dashboard/farmer-list/users-profile/<int:user_id>/", users_profile, name="users_profile"),
    path("admin-dashboard/buyer-list/", buyer_list, name="buyer_list"),
    path("admin-dashboard/products/", views.products, name="products"),
    path("admin-dashboard/cart_list/", views.cart_list, name="cart_list"),
    path("admin-dashboard/paid_list/", views.paid_list, name='paid_list'),

    path('logs/delete-all/<str:action>/', views.delete_all_activity_logs, name='delete_all_activity_logs'),


    path('activity_log_filtered/<str:action>/', views.activity_log_filtered, name='activity_log_filtered'),
    path('activity_log/<int:pk>/', views.activity_log_detail, name='activity_log_detail'),
    path('activity_log/<int:log_id>/<str:action>/delete/', views.activity_log_delete, name='activity_log_delete'),




    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('register/', register, name='register'),


    path('reset_password/', views.password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', views.reset_password_confirm, name='password_reset_confirm'),


]
