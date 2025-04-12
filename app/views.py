from urllib import response
import uuid
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Cart, Paid, Log
from .forms import UserRegistrationForm, ProductForm
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from decimal import Decimal
from django.db import transaction
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import update_session_auth_hash
import requests
from django.http import JsonResponse
from django.conf import settings
import json
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from app.models import CustomUser
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.timezone import now
from datetime import timedelta, timezone
from .models import Log




def home_view(request):
    if request.user.is_authenticated:
        logout(request)
        return render(request, 'home.html')
    else:
        return render(request, 'home.html') 


#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#Reset Password -------------------------------------------------------------------------------------------------------------------------


def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "No user found with this email address.")
            return redirect("password_reset_request")

        # Generate password reset token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Render the email template
        message = render_to_string("registration/emails/reset_password_email.html", {
            'user': user,
            'domain': request.get_host(),
            'uid': uid,
            'token': token,
            "protocol": "https" if request.is_secure() else "http"
        })

        # Send the email
        email_message = EmailMessage("Password Reset Request", message, to=[email])
        email_message.content_subtype = "html"  # Set the email format to HTML
        email_message.send()

        messages.success(request, "A password reset link has been sent to your email.")
        return redirect("login")

    return render(request, 'registration/reset/form_password_reset.html')


def reset_password_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (CustomUser.DoesNotExist, ValueError, TypeError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password1 = request.POST.get("new_password1")
            new_password2 = request.POST.get("new_password2")

            if new_password1 and new_password2:
                if new_password1 == new_password2:
                    user.set_password(new_password1)
                    user.save()
                    update_session_auth_hash(request, user)  # Keeps the user logged in after password change
                    messages.success(request, "Your password has been successfully reset. You can now log in.")
                    return redirect("login")
                else:
                    messages.error(request, "Passwords do not match.")
            else:
                messages.error(request, "Both password fields are required.")

        return render(request, "registration/reset/confirm_password_reset.html", {"validlink": True})

    else:
        messages.error(request, "The password reset link is invalid or has expired.")
        return render(request, "registration/password_reset_confirm.html", {"validlink": False})


def send_reset_email(request, user):
    subject = "Reset Your Password"
    message = render_to_string('reset_password_email.html', {
        'user': user,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })

    email = EmailMessage(subject, message, to=[user.email])
    email.content_subtype = "html"  # Set email format to HTML
    email.send()



#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#Register -------------------------------------------------------------------------------------------------------------------------

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Thank you for your email confirmation. Now you can login your account.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid!")
    return redirect('product_list')



def activateEmail(request, user, to_email):
    mail_subject = "Activate your user account."
    
    # Render the HTML template
    message = render_to_string("registration/emails/template_activate_account.html", {
        'user': user.first_name,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        "protocol": 'https' if request.is_secure() else 'http'
    })
    
    # Create an email message and set content type to HTML
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = "html"  # This ensures the email is sent as HTML
    
    if email.send():
        messages.success(request, f'Dear <b>{user}</b>, please check your email <b>{to_email}</b> inbox and click on \
                the received activation link to confirm and complete the registration. <b>Note:</b> Check your spam folder.')
    else:
        messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.')



def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))

            # Log the registration attempt
            Log.objects.create(
                message=f"User registration attempted for {user.username}. Activation email sent.",
                log_type="info"
            )

            return redirect('login')
        else:
            for error in list(form.errors.values()):
                messages.error(request, error)
                # Log invalid registration attempt
                Log.objects.create(
                    message=f"Invalid registration form submission. Errors: {error}",
                    log_type="warning"
                )

    else:
        form = UserRegistrationForm()

    return render(
        request=request,
        template_name="registration/register_email.html",
        context={"form": form}
    )

#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
# log in and log out----------------------------------------------------------------------------------------------

def custom_logout(request):
    user = request.user
    logout(request)
    messages.info(request, "Logged out successfully!")
    if user.is_authenticated: #in case logout failed for some reason, do not log.
        Log.objects.create(
            message=f"User {user.username} logged out.",
            log_type="info"
        )
        if user.is_superuser:  # Check if the user is a superuser (admin)
            return redirect("admin_login")
    return redirect("login")

def custom_login(request):
    if request.user.is_authenticated:
        return redirect_based_on_role(request.user, request)  # Pass request

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not user.is_activated: # Check if user is activated
                    messages.error(request, "Your account is not activated by admins!")
                    Log.objects.create(
                        message=f"Failed login attempt for username: {username}. Account not activated by admin!",
                        log_type="warning"
                    )
                    return render(
                        request,
                        template_name="registration/login.html",
                        context={"form": form}
                    )
                login(request, user)
                Log.objects.create(
                    message=f"User {user.username} logged in.",
                    log_type="info"
                )
                return redirect_based_on_role(user, request)
            else:
                messages.error(request, "Invalid username or password.")
                Log.objects.create(
                    message=f"Failed login attempt for username: {username}.",
                    log_type="warning"
                )
        else:
            for error in form.errors.values():
                Log.objects.create(
                    message=f"Invalid login form submission. Errors: {error}",
                    log_type="warning"
                )
                messages.error(request, error)
    else:
        form = AuthenticationForm()

    return render(
        request,
        template_name="registration/login.html",
        context={"form": form}
    )

def redirect_based_on_role(user, request):
    if user.role == 'farmer':
        messages.success(request, f"<i>Welcome</i> <b>{user.username}</b>! You have been logged in as <b>Farmer</b>")
        return redirect('product_list')
    elif user.role == 'buyer':
        messages.success(request, f"<i>Welcome</i> <b>{user.username}</b>! You have been logged in as <b>Buyer</b>")
        return redirect('product_list')
    else:
        logout(request)
        messages.error(request, "You are not authorized to access the website")
        return redirect('/')
    
#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
# Product-----------------------------------------------------------------------------------------------------------------

@login_required
def product_list(request):
    user = request.user
    products = Product.objects.none()  # Default empty queryset

    # Get search, category, and sorting filters
    search_query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()
    sort_by = request.GET.get('sort', '').strip()  # Existing sort option, if any

    # Role-based product filtering
    if user.role == 'farmer':
        products = Product.objects.filter(farmer=user)
        total_products = products.count()
        categories = (
            Product.objects.filter(farmer=user)
            .values('product_category')
            .annotate(count=Count('id'))
            .order_by('product_category')
        )
    elif user.role == 'buyer':
        products = Product.objects.all()
        total_products = products.count()
        categories = (
            Product.objects.all()
            .values('product_category')
            .annotate(count=Count('id'))
            .order_by('product_category')
        )
    # elif request.user.is_superuser:
    #     products = Product.objects.all()
    #     total_products = products.count()
    #     categories = (
    #         Product.objects.values('product_category')
    #         .annotate(count=Count('id'))
    #         .order_by('product_category')
    #     )
    else:
        categories = Product.objects.none()  # Default to empty if no role is found
        total_products = 0

    # Apply category filter to products
    if selected_category:
        products = products.filter(product_category=selected_category)
        # Only default to 'price' sort if no sort option is provided
        if not sort_by:
            sort_by = 'price'

    # Apply search filter if query exists
    if search_query:
        products = products.filter(Q(product_name__icontains=search_query))

    # Apply sorting based on sort_by GET parameter (if set)
    if sort_by:
        if sort_by == 'alphabetical':
            products = products.order_by('product_name')
        elif sort_by == 'latest':
            products = products.order_by('-created_at')
        elif sort_by == 'price':
            products = products.order_by('product_price')

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
        'total_products': total_products,
        'sort_by': sort_by,
    }
    return render(request, 'farmer/products_list.html', context)


import random
import string

def generate_product_id():
    # Generate a random 6-digit number
    random_digits = ''.join(random.choices(string.digits, k=6))
    return f"PRODUCT{random_digits}"
    
@login_required
def add_product(request):
    user = request.user
    if user.role != 'farmer':
        messages.error(request, f"You are Not Autorized to ADD PRODUCT")
        return redirect('product_list')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.farmer = request.user  # Assign the current user as the farmer
            
            # Generate unique product ID
            while True:
                product_id = generate_product_id()
                if not Product.objects.filter(product_id=product_id).exists():
                    product.product_id = product_id
                    break
            
            product.save()
            messages.success(request, f"Product created successfully. Product ID: {product.product_id}")
            # Log the product creation
            Log.objects.create(
                message=f"Farmer {request.user.username} added product: {product.product_name} (ID: {product.product_id})",
                log_type="success"
            )
            return redirect('product_list')  # Redirect to your product list view or any other page
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ProductForm()
    
    return render(request, 'farmer/add_product.html', {'form': form})



from math import radians, cos, sin, asin, sqrt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models import Product, Log

#coordinates: 
LOCATION_COORDINATES = {
    # Addis Ababa (Subcities)
    ("Addis Ababa", "Addis Ketema"): (38.73, 9.03),
    ("Addis Ababa", "Akaky Kaliti"): (38.80, 8.90),
    ("Addis Ababa", "Arada"): (38.75, 9.03),
    ("Addis Ababa", "Bole"): (38.80, 8.99),
    ("Addis Ababa", "Gulele"): (38.73, 9.06),
    ("Addis Ababa", "Kirkos"): (38.76, 9.01),
    ("Addis Ababa", "Kolfe Keranio"): (38.68, 9.01),
    ("Addis Ababa", "Lideta"): (38.74, 9.02),
    ("Addis Ababa", "Nifas Silk-Lafto"): (38.73, 8.97),
    ("Addis Ababa", "Yeka"): (38.82, 9.04),

    # Afar
    ("Afar", "Semera"): (41.01, 11.79),
    ("Afar", "Awash"): (40.17, 8.99),
    ("Afar", "Asayita"): (41.44, 11.57),
    ("Afar", "Logia"): (40.97, 11.73),
    ("Afar", "Dubti"): (41.09, 11.73),

    # Amhara
    ("Amhara", "Bahir Dar"): (37.38, 11.58),
    ("Amhara", "Gondar"): (37.47, 12.60),
    ("Amhara", "Dessie"): (39.63, 11.13),
    ("Amhara", "Debre Markos"): (37.73, 10.33),
    ("Amhara", "Kombolcha"): (39.74, 11.09),
    ("Amhara", "Debre Birhan"): (39.53, 9.68),
    ("Amhara", "Weldiya"): (39.59, 11.83),
    ("Amhara", "Lalibela"): (39.04, 12.03),
    ("Amhara", "Finote Selam"): (37.27, 10.70),
    ("Amhara", "Debre Tabor"): (38.02, 11.85),
    ("Amhara", "Guba Lafto"): (39.59, 11.83),
    ("Amhara", "Bati"): (40.02, 11.19),
    ("Amhara", "Sekota"): (39.03, 12.63),
    ("Amhara", "Dabat"): (37.77, 12.98),
    ("Amhara", "Debre Sina"): (39.77, 9.85),

    # Benishangul-Gumuz
    ("Benishangul-Gumuz", "Assosa"): (34.53, 10.07),
    ("Benishangul-Gumuz", "Bambasi"): (34.73, 9.75),
    ("Benishangul-Gumuz", "Mankush"): (35.20, 10.92),
    ("Benishangul-Gumuz", "Gilgel Beles"): (36.10, 10.88),

    # Dire Dawa
    ("Dire Dawa", "Dire Dawa"): (41.87, 9.59),
    ("Dire Dawa", "Deder"): (41.44, 9.31),
    ("Dire Dawa", "Chiro"): (40.87, 9.07),
    ("Dire Dawa", "Babile"): (42.33, 9.22),
    ("Dire Dawa", "Mieso"): (40.75, 9.23),
    ("Dire Dawa", "Kersa"): (41.60, 9.35),

    # Gambela
    ("Gambela", "Gambela"): (34.58, 8.25),
    ("Gambela", "Abobo"): (34.53, 7.85),
    ("Gambela", "Itang"): (34.27, 8.17),
    ("Gambela", "Mettu"): (35.58, 8.30),
    ("Gambela", "Lare"): (33.90, 8.28),
    ("Gambela", "Jikawo"): (33.37, 8.65),
    ("Gambela", "Akobo"): (33.05, 7.80),

    # Harari
    ("Harari", "Harar"): (42.12, 9.31),
    ("Harari", "Babile"): (42.33, 9.22),
    ("Harari", "Chiro"): (40.87, 9.07),
    ("Harari", "Deder"): (41.44, 9.31),
    ("Harari", "Harar Meda"): (39.00, 8.77),
    ("Harari", "Kersa"): (41.60, 9.35),
    ("Harari", "Mieso"): (40.75, 9.23),

    # Oromia
    ("Oromia", "Adama"): (39.27, 8.55),
    ("Oromia", "Jimma"): (36.83, 7.67),
    ("Oromia", "Ambo"): (37.85, 8.98),
    ("Oromia", "Shashamene"): (38.60, 7.20),
    ("Oromia", "Bishoftu"): (38.98, 8.75),
    ("Oromia", "Nekemte"): (36.55, 9.08),
    ("Oromia", "Asella"): (39.12, 7.95),
    ("Oromia", "Hossana"): (37.85, 7.55),
    ("Oromia", "Woliso"): (37.97, 8.53),
    ("Oromia", "Agaro"): (36.58, 7.85),
    ("Oromia", "Bale Robe"): (40.00, 7.13),
    ("Oromia", "Bedele"): (36.35, 8.45),
    ("Oromia", "Gimbi"): (35.83, 9.17),
    ("Oromia", "Bako"): (37.05, 9.13),
    ("Oromia", "Dembi Dolo"): (34.80, 8.53),
    ("Oromia", "Fincha"): (37.38, 9.58),
    ("Oromia", "Gindhir"): (40.70, 6.87),
    ("Oromia", "Kofele"): (38.78, 7.07),
    ("Oromia", "Mettu"): (35.58, 8.30),
    ("Oromia", "Shakiso"): (38.90, 5.78),
    ("Oromia", "Yabelo"): (38.08, 4.88),

    # Sidama
    ("Sidama", "Hawassa"): (38.48, 7.05),
    ("Sidama", "Yirgalem"): (38.42, 6.75),
    ("Sidama", "Hagere Selam"): (38.53, 6.48),
    ("Sidama", "Bensa"): (39.00, 6.67),
    ("Sidama", "Arsi Negele"): (38.70, 7.35),

    # SNNP
    ("SNNP", "Arba Minch"): (37.55, 6.03),
    ("SNNP", "Wolayita Sodo"): (37.75, 6.85),
    ("SNNP", "Hossana"): (37.85, 7.55),
    ("SNNP", "Jinka"): (36.57, 5.78),
    ("SNNP", "Sawla"): (36.88, 6.30),
    ("SNNP", "Boditi"): (37.87, 6.97),
    ("SNNP", "Areka"): (37.70, 7.07),
    ("SNNP", "Chencha"): (37.57, 6.25),
    ("SNNP", "Dilla"): (38.31, 6.41),

    # Somali
    ("Somali", "Jijiga"): (42.80, 9.35),
    ("Somali", "Dollo"): (41.95, 4.17),
    ("Somali", "Degehabur"): (43.57, 8.22),
    ("Somali", "Gode"): (43.55, 5.95),
    ("Somali", "Kebri Dehar"): (44.27, 6.73),
    ("Somali", "Fik"): (42.28, 8.08),
    ("Somali", "Warder"): (45.35, 6.97),

    # Tigray
    ("Tigray", "Axum"): (38.72, 14.13),
    ("Tigray", "Adigrat"): (39.46, 14.28),
    ("Tigray", "Shire"): (38.29, 14.10),
    ("Tigray", "Alamata"): (39.55, 12.42),
    ("Tigray", "Wukro"): (39.60, 13.78),
    ("Tigray", "Adwa"): (38.90, 14.17),
    ("Tigray", "Hawzen"): (39.43, 13.98),
    ("Tigray", "Mekele"): (39.47, 13.50),
    ("Tigray", "Enderta"): (39.47, 13.50),
    ("Tigray", "Tsegede"): (37.53, 13.60),
    ("Tigray", "Laelay Adiyabo"): (38.13, 14.38),
    ("Tigray", "Degua Tembien"): (39.17, 13.65),
    ("Tigray", "Saharti Samre"): (39.10, 13.23),
    ("Tigray", "Ofla"): (39.52, 12.50),
    ("Tigray", "Kilte Awlalo"): (39.60, 13.78),
}


import openrouteservice
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Product, Log

ors_client = openrouteservice.Client(key='5b3ce3597851110001cf6248672144f6a5714e8988cc68cf90382422')



def get_coords(region, zone):
    return LOCATION_COORDINATES.get((region, zone))


def get_distance_km(start_coords, end_coords):
    try:
        route = ors_client.directions(
            coordinates=[start_coords, end_coords],  # [lon, lat]
            profile='driving-car',
            format='geojson'
        )
        distance_m = route['features'][0]['properties']['segments'][0]['distance']
        print(f"Distance in meters: {distance_m}")
        return round(distance_m / 1000, 2)  # Return in kilometers
    except Exception as e:
        print(f"Distance retrieval failed: {e}")
        return 0


def calculate_transport_fee(distance_km):
    if 1 <= distance_km <= 10:
        return 3000
    elif 10 < distance_km <= 50:
        return 5000
    elif 50 < distance_km <= 100:
        return 8000
    elif 100 < distance_km <= 200:
        return 15000
    elif 200 < distance_km <= 300:
        return 20000
    elif 300 < distance_km <= 400:
        return 25000
    elif 400 < distance_km <= 500:
        return 30000
    elif 500 < distance_km <= 600:
        return 35000
    elif 600 < distance_km <= 700:
        return 40000
    elif 700 < distance_km <= 800:
        return 45000
    elif 300 < distance_km <= 400:
        return 25000
    elif 400 < distance_km <= 500:
        return 30000
    elif 500 < distance_km <= 600:
        return 35000
    elif 600 < distance_km <= 700:
        return 40000
    elif 700 < distance_km <= 800:
        return 45000
    elif 300 < distance_km <= 400:
        return 25000
    elif 400 < distance_km <= 500:
        return 30000
    elif 500 < distance_km <= 600:
        return 35000
    elif 600 < distance_km <= 700:
        return 40000
    elif 700 < distance_km <= 800:
        return 45000
    elif 300 < distance_km <= 400:
        return 25000
    elif 400 < distance_km <= 500:
        return 30000
    elif 500 < distance_km <= 600:
        return 35000
    elif 600 < distance_km <= 700:
        return 40000
    elif 700 < distance_km <= 800:
        return 45000
    elif 800 < distance_km <= 900:
        return 50000
    elif 900 < distance_km <= 1000:
        return 55000
    elif 1000 < distance_km <= 1500:
        return 65000
    elif 1500 < distance_km <= 2000:
        return 75000
    elif 2000 < distance_km <= 2500:
        return 85000
    elif 2500 < distance_km <= 3000:
        return 95000
    else:
        return 100000


@login_required
def product_detail(request, product_id):
    selected_product_id = request.GET.get('selected', product_id)
    product = get_object_or_404(Product, id=selected_product_id)

    # Get coordinates from predefined dictionary
    farmer_coords = get_coords(product.farmer.region, product.farmer.zone)
    buyer_coords = get_coords(request.user.region, request.user.zone)

    transport_fee = 0
    if farmer_coords and buyer_coords:
        distance_km = get_distance_km(farmer_coords, buyer_coords)
        transport_fee = calculate_transport_fee(distance_km)

    Log.objects.create(
        message=f"Buyer {request.user.username} viewed product details: {product.product_name}",
        log_type="info"
    )

    context = {
        'selected_product': product,
        'transport_fee': transport_fee,
        'distance_km' : distance_km
    }
    return render(request, 'buyer/product_detail.html', context)






#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
# Cart adding-----------------------------------------------------------------------------------------------------------------
from django.utils import timezone


@login_required
def add_to_cart(request):
    if request.method == 'POST':
        # Retrieve posted data
        product_id = request.POST.get('product_id')
        try:
            quantity = int(request.POST.get('quantity', 100))
        except ValueError:
            messages.error(request, "Invalid quantity.")
            return redirect('product_detail', product_id=product_id)
        
        # Get the product from the database
        product = get_object_or_404(Product, id=product_id)
        
        # Validate the ordered quantity
        if quantity < 100:
            messages.error(request, "Minimum order quantity is 100.")
            return redirect('product_detail', product_id=product_id)
        if quantity > int(product.product_quantity):
            messages.error(request, "Requested quantity exceeds available stock.")
            return redirect('product_detail', product_id=product_id)
        
        # Get coordinates from predefined dictionary
        farmer_coords = get_coords(product.farmer.region, product.farmer.zone)
        buyer_coords = get_coords(request.user.region, request.user.zone)

        transport_fee = 0
        if farmer_coords and buyer_coords:
            distance_km = get_distance_km(farmer_coords, buyer_coords)
            transport_fee = calculate_transport_fee(distance_km)

        # Calculate total price; using Decimal for arithmetic accuracy.
        try:
            price_per_kg = Decimal(product.product_price)
        except Exception:
            price_per_kg = Decimal('0.00')
        total_price = (Decimal(quantity) * price_per_kg)+ transport_fee
        
        # Copy key fields from the product to the cart record.
        # Adjust the field names as per your Product model.
        order_name = product.product_name  
        order_price = price_per_kg  
        order_image = product.product_image  
        order_category = product.product_category
        created_at = product.created_at
        product_id = product.product_id

       

        # Update product quantity and create cart record atomically
        with transaction.atomic():
            remaining_quantity = int(product.product_quantity) - quantity
            
            # Create the Cart record with copied product data.
            Cart.objects.create(
                product_id=product_id,
                order_name=order_name,
                order_quantity=Decimal(quantity),
                order_price=order_price,
                order_image=order_image,
                order_category=order_category,
                total_price=total_price,
                distance_km=distance_km,
                transport_fee=transport_fee,
                farmer=product.farmer,
                buyer=request.user,
                created_at=created_at,
                ordered_at=timezone.now(),
            )

            if remaining_quantity == 0:
                product.delete()
            else:
                product.product_quantity = str(remaining_quantity)
                product.save()

        messages.success(request, f"Product added to cart with transport fee of {transport_fee}!")
        Log.objects.create(
            message=f"Buyer {request.user.username} added {quantity} of {product.product_name} to cart.",
            log_type="success"
        )
        return redirect('cart')
    else:
        messages.error(request, "Invalid request.")
        return redirect('product_list')



@login_required
def cart(request):
    if hasattr(request.user, 'role'):  # Ensure the user has a role attribute
        if request.user.role == 'buyer':
            cart_items = Cart.objects.filter(buyer=request.user)
        elif request.user.role == 'farmer':
            cart_items = Cart.objects.filter(farmer=request.user)
        else:
            cart_items = Cart.objects.none()  # Return an empty queryset if role is undefined
    else:
        cart_items = Cart.objects.none()  # Handle cases where the role attribute is missing

    return render(request, 'buyer/cart.html', {'cart_items': cart_items})


#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
# paying-----------------------------------------------------------------------------------------------------------------
@login_required
def payment_detail(request, item_id):
    # Fetch the item from the database using the passed item_id
    item = get_object_or_404(Cart, id=item_id)
    
    # Generate a unique transaction reference
    trx_ref = f"Order-{uuid.uuid4().hex[:10]}-{item_id}"
    
    context = {
        'item': item,
        'trx': trx_ref
    }
    return render(request, 'buyer/payment_detail.html', context)


CHAPA_SECRET_KEY = "CHASECK_TEST-VPikVFcVYY4wTq4MRgonDUZujkWctaH9"

@csrf_exempt
def chapa_callback(request, item_id):
    # Add CORS headers
    response = JsonResponse({"status": "pending"})
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    # Handle preflight requests
    if request.method == "OPTIONS":
        return response
        
    # Get the transaction reference from the request
    trx_ref = request.GET.get('trx_ref')
    if not trx_ref:
        # Try alternate parameter name
        trx_ref = request.GET.get('tx_ref')
    status = request.GET.get('status')
    
    print(f"Received callback - trx_ref: {trx_ref}, status: {status}, query params: {request.GET}")
    
    if not trx_ref:
        error_msg = "Missing transaction reference"
        print(f"❌ {error_msg}")
        response = JsonResponse({"error": error_msg}, status=400)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Verify the transaction with Chapa
    verification_url = f"https://api.chapa.co/v1/transaction/verify/{trx_ref}"
    headers = {"Authorization": f"Bearer {CHAPA_SECRET_KEY}"}

    try:
        verify_response = requests.get(verification_url, headers=headers)
        print(f"Chapa verification response: {verify_response.status_code}, {verify_response.text}")

        if verify_response.status_code == 200:
            data = verify_response.json()

            # Check if the payment was successful
            if data.get("status") == "success":
                print(f"✅ Payment verified for trx_ref: {trx_ref}")

                try:
                    # Get the Cart item based on the item_id passed in the URL
                    cart_item = get_object_or_404(Cart, id=item_id)

                    # Store payment data in Paid model
                    paid_item = Paid.objects.create(
                        paid_product_name=cart_item.order_name,  
                        paid_product_quantity=cart_item.order_quantity,  
                        paid_product_price=cart_item.order_price,  
                        paid_product_image=cart_item.order_image,  
                        paid_product_category=cart_item.order_category,  
                        total_price=cart_item.total_price,
                        distance_km=cart_item.distance_km,
                        transport_fee=cart_item.transport_fee,
                        created_at=cart_item.created_at, 
                        ordered_at=cart_item.ordered_at,
                        paid_at=timezone.now(),
                        farmer=cart_item.farmer,  
                        buyer=cart_item.buyer,  
                        transaction_reference=trx_ref,
                        payment_status='pending',  
                    )

                    # Create a success log
                    Log.objects.create(
                        message=f"Payment successful for order {cart_item.order_name}",
                        log_type="success"
                    )

                    # Remove the cart item after successful payment
                    cart_item.delete()

                    response = JsonResponse({
                        "status": "success",
                        "message": "Payment verified successfully",
                        "redirect_url": "/paid/"
                    })
                    response["Access-Control-Allow-Origin"] = "*"
                    return response
                except Exception as e:
                    error_msg = f"Error processing payment: {str(e)}"
                    print(f"❌ {error_msg}")
                    Log.objects.create(
                        message=error_msg,
                        log_type="danger"
                    )
                    response = JsonResponse({"error": error_msg}, status=500)
                    response["Access-Control-Allow-Origin"] = "*"
                    return response
            else:
                error_msg = f"Payment verification failed: {data.get('message', 'Unknown error')}"
                print(f"❌ {error_msg}")
                Log.objects.create(
                    message=f"Payment failed: {error_msg}",
                    log_type="danger"
                )
                response = JsonResponse({"error": error_msg}, status=400)
                response["Access-Control-Allow-Origin"] = "*"
                return response
        else:
            error_msg = f"Chapa verification request failed with status {verify_response.status_code}"
            print(f"⚠️ {error_msg}")
            Log.objects.create(
                message=error_msg,
                log_type="warning"
            )
            response = JsonResponse({"error": error_msg}, status=400)
            response["Access-Control-Allow-Origin"] = "*"
            return response
    except Exception as e:
        error_msg = f"Error during payment verification: {str(e)}"
        print(f"❌ {error_msg}")
        Log.objects.create(
            message=error_msg,
            log_type="danger"
        )
        response = JsonResponse({"error": error_msg}, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        return response

def chapa_return(request):
    return render(request, "buyer/paid.html")


@login_required
def paid(request):
    user = request.user

    # Ensure the user has a role attribute before proceeding
    if hasattr(user, 'role'):
        if user.role == 'buyer':
            paid_items = Paid.objects.filter(buyer=user)
            template = 'buyer/paid.html'
        elif user.role == 'farmer':
            paid_items = Paid.objects.filter(farmer=user)
            template = 'buyer/paid.html'
        else:
            paid_items = Paid.objects.none()
            template = 'no_access.html'  # Optional: Create a template for unauthorized roles
    else:
        paid_items = Paid.objects.none()

    return render(request, template, {'paid_items': paid_items})

@login_required
def paid_detail(request, item_id):
    # Fetch the item from the database using the passed item_id
    item = get_object_or_404((Paid), id=item_id)

    # Pass the item to the template for rendering
    return render(request, 'buyer/paid_detail.html', {'item': item})


#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#admin --------------------------------------------------------------------------------------------------------------





from django.contrib.auth import authenticate, login


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')  # Redirect to admin panel if already logged in
    elif request.user.is_authenticated and not request.user.is_staff:
        logout(request)
        return redirect('/')
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:  # Only allow staff users
            login(request, user)
            Log.objects.create(
                message=f"Admin {user.username} logged in.",
                log_type="success"
            )
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not an admin user.")
            Log.objects.create(
                message=f"Failed admin login attempt for username: {username}.",
                log_type="warning"
            )

    return render(request, "dashboard/admin_login.html")



@login_required
def admin_dashboard(request):
    product_count = Product.objects.count()
    cart_count = Cart.objects.count()
    paid_count = Paid.objects.count()
    this_month = now().month
    this_year = now().year
    product_count_month = Product.objects.filter(created_at__month=this_month, created_at__year=this_year).count()
    cart_count_month = Cart.objects.filter(created_at__month=this_month, created_at__year=this_year).count()
    today = now().date()
    product_count_day = Product.objects.filter(created_at__date=today).count()
    cart_count_day = Cart.objects.filter(created_at__date=today).count()
    time_24_hours_ago = now() - timedelta(hours=24)
    product_count_24_hours = Product.objects.filter(created_at__gte=time_24_hours_ago).count()
    cart_count_24_hours = Cart.objects.filter(created_at__gte=time_24_hours_ago).count()
    total_product_value = Product.objects.annotate(total_value=ExpressionWrapper(F('product_quantity') * F('product_price'), output_field=DecimalField())).aggregate(total_value_sum=Sum('total_value'))['total_value_sum'] or 0
    total_cart_value = Cart.objects.aggregate(cart_total_value_sum=Sum(F('order_quantity') * F('order_price')))['cart_total_value_sum'] or 0
    total_paid_value = Paid.objects.aggregate(total_paid_sum=Sum('total_price'))['total_paid_sum'] or 0
    #total_paid_value = Paid.objects.filter(payment_status='pending').aggregate(total_paid_sum=Sum('total_price'))['total_paid_sum'] or 0
    total_transport_fee = Paid.objects.aggregate(total=Sum('transport_fee'))['total'] or 0
    total_product_cost = total_paid_value-total_transport_fee

    total_users = CustomUser.objects.count()
    total_buyers = CustomUser.objects.filter(role='buyer').count()
    total_farmers = CustomUser.objects.filter(role='farmer').count()

    active_users = CustomUser.objects.filter(is_active=True).count()
    inactive_users = CustomUser.objects.filter(is_active=False).count()
    verified_users = CustomUser.objects.filter(is_activated=True).count()

    active_buyers = CustomUser.objects.filter(role='buyer', is_active=True).count()
    inactive_buyers = CustomUser.objects.filter(role='buyer', is_active=False).count()
    verified_buyers = CustomUser.objects.filter(role='buyer', is_activated=True).count()

    active_farmers = CustomUser.objects.filter(role='farmer', is_active=True).count()
    inactive_farmers = CustomUser.objects.filter(role='farmer', is_active=False).count()
    verified_farmers = CustomUser.objects.filter(role='farmer', is_activated=True).count()

    recent_logs = Log.objects.filter(timestamp__date=today).order_by('-timestamp')[:10]

    context = {
        'product_count': product_count,
        'cart_count': cart_count,
        'paid_count': paid_count,
        'total_transport_fee': total_transport_fee,
        'total_product_cost': total_product_cost,
        'product_count_month': product_count_month,
        'cart_count_month': cart_count_month,
        'product_count_day': product_count_day,
        'cart_count_day': cart_count_day,
        'product_count_24_hours': product_count_24_hours,
        'cart_count_24_hours': cart_count_24_hours,
        'total_product_value': total_product_value,
        'total_paid_value': total_paid_value,
        'total_cart_value': total_cart_value,
        'total_users': total_users,
        'total_buyers': total_buyers,
        'total_farmers': total_farmers,
        'recent_logs': recent_logs,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'verified_users': verified_users,
        'active_buyers': active_buyers,
        'inactive_buyers': inactive_buyers,
        'verified_buyers': verified_buyers,
        'active_farmers': active_farmers,
        'inactive_farmers': inactive_farmers,
        'verified_farmers': verified_farmers,
    }
    return render(request, "dashboard/index.html", context)


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_names = Product.objects.values_list('product_name', flat=True).distinct()
    farmers = CustomUser.objects.filter(role='farmer') 

    if request.method == 'POST':
        product.product_name = request.POST.get('product_name')
        product.product_quantity = request.POST.get('product_quantity')
        product.product_price = request.POST.get('product_price')
        product.product_category = request.POST.get('product_category')

        if 'product_image' in request.FILES:
            product.product_image = request.FILES['product_image']

        # Check if the 'farmer_id' is blank, if so set farmer to None
        farmer_id = request.POST.get('farmer_id')
        if farmer_id:
            product.farmer = CustomUser.objects.get(id=farmer_id)
        else:
            product.farmer = None  # If no farmer selected, set it to None

        product.save()
        messages.success(request, "Product updated successfully.")
        return redirect('products')  # Back to product list

    return render(request, 'dashboard/edit_product.html', {
        'product': product,
        'product_names': product_names,
        'farmers': farmers,
    })
@login_required
def delete_product(request, product_id):
    # Get the product by ID, or return a 404 if not found
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.delete()  # Delete the product
        messages.success(request, 'Product deleted successfully.')
        return redirect('products')  # Redirect to the products list page
    

@login_required
def edit_cart(request, cart_id):
    cart = get_object_or_404(Cart, id=cart_id)
    cart_names = Cart.objects.values_list('order_name', flat=True).distinct()  # Fix field name to match model
    farmers = CustomUser.objects.filter(role='farmer')  # Fetch farmers based on their role
    buyers = CustomUser.objects.filter(role='buyer')  # Fetch buyers based on their role

    if request.method == 'POST':
        # Get values from the form
        order_name = request.POST.get('order_name')
        order_quantity = Decimal(request.POST.get('order_quantity'))  # Convert to Decimal
        order_price = Decimal(request.POST.get('order_price'))  # Convert to Decimal
        order_category = request.POST.get('order_category')
        transport_fee = Decimal(request.POST.get('transport_fee') or 0)
        distance_km = Decimal(request.POST.get('distance_km') or 0)


        # Update the cart object
        cart.order_name = order_name
        cart.order_quantity = order_quantity
        cart.order_price = order_price
        cart.order_category = order_category
        cart.transport_fee = transport_fee
        cart.distance_km = distance_km

        # Handle image upload if present
        if 'order_image' in request.FILES:
            cart.order_image = request.FILES['order_image']

        # Update farmer if selected
        farmer_id = request.POST.get('farmer_id')
        if farmer_id:
            cart.farmer = CustomUser.objects.get(id=farmer_id)
        else:
            cart.farmer = None  # If no farmer selected, set it to None

        # Update buyer if selected
        buyer_id = request.POST.get('buyer_id')
        if buyer_id:
            cart.buyer = CustomUser.objects.get(id=buyer_id)
        else:
            cart.buyer = None  # If no buyer selected, set it to None

        # Update total price based on quantity and price
        cart.total_price = (cart.order_quantity * cart.order_price) + cart.transport_fee

        cart.save()
        messages.success(request, "Cart updated successfully.")
        return redirect('cart_list')  # Redirect to cart list or wherever you need

    return render(request, 'dashboard/edit_cart.html', {
        'cart': cart,
        'cart_names': cart_names,
        'farmers': farmers,
        'buyers': buyers,
    })


@login_required
def delete_cart(request, cart_id):
    # Retrieve the cart item or return a 404 error if it does not exist
    cart = get_object_or_404(Cart, id=cart_id)

    if request.method == 'POST':
        cart.delete()  # Deletes the cart item
        messages.success(request, 'Cart item deleted successfully.')
        return redirect('cart_list')  # Redirect to cart list page after deletion
    
@login_required
def edit_paid(request, paid_id):
    # Get the Paid record by ID
    paid = get_object_or_404(Paid, id=paid_id)
    paid_names = Paid.objects.values_list('paid_product_name', flat=True).distinct()  # Ensure this matches the field you want to filter by
    farmers = CustomUser.objects.filter(role='farmer')  # Filter for farmers based on role
    buyers = CustomUser.objects.filter(role='buyer')  # Filter for buyers based on role

    if request.method == 'POST':
        # Get updated values from the form
        paid_product_name = request.POST.get('paid_product_name')
        paid_product_quantity = Decimal(request.POST.get('paid_product_quantity'))  # Convert to Decimal
        paid_product_price = Decimal(request.POST.get('paid_product_price'))  # Convert to Decimal
        paid_product_category = request.POST.get('paid_product_category')
        paid.transport_fee = Decimal(request.POST.get('transport_fee') or 0)
        paid.distance_km = Decimal(request.POST.get('distance_km') or 0)

        # Update paid fields
        paid.paid_product_name = paid_product_name
        paid.paid_product_quantity = paid_product_quantity
        paid.paid_product_price = paid_product_price
        paid.paid_product_category = paid_product_category

        # Handle image upload if there is a new image
        if 'paid_product_image' in request.FILES:
            paid.paid_product_image = request.FILES['paid_product_image']

        # Update farmer if selected
        farmer_id = request.POST.get('farmer_id')
        if farmer_id:
            paid.farmer = CustomUser.objects.get(id=farmer_id)
        else:
            paid.farmer = None  # If no farmer selected, set to None

        # Update buyer if selected
        buyer_id = request.POST.get('buyer_id')
        if buyer_id:
            paid.buyer = CustomUser.objects.get(id=buyer_id)
        else:
            paid.buyer = None  # If no buyer selected, set to None

        # Update total price based on quantity and price
        paid.total_price = (paid.paid_product_quantity * paid.paid_product_price) + paid.transport_fee

        # If payment status or transaction reference is updated
        payment_status = request.POST.get('payment_status')
        if payment_status:
            paid.payment_status = payment_status
        
        transaction_reference = request.POST.get('transaction_reference')
        if transaction_reference:
            paid.transaction_reference = transaction_reference

        paid.save()
        messages.success(request, "Paid order updated successfully.")
        return redirect('paid_list')  # Redirect to the paid orders list or another appropriate page

    return render(request, 'dashboard/edit_paid.html', {
        'paid': paid,
        'paid_names': paid_names,
        'farmers': farmers,
        'buyers': buyers,
    })
@login_required
def delete_paid(request, paid_id):
    # Retrieve the cart item or return a 404 error if it does not exist
    paid = get_object_or_404(Paid, id=paid_id)

    if request.method == 'POST':
        paid.delete()  # Deletes the cart item
        messages.success(request, 'Paid item deleted successfully.')
        return redirect('paid_list')  # Redirect to cart list page after deletion


@login_required
def farmer_list(request):
    farmers = CustomUser.objects.filter(role='farmer')  # Assuming `user_type` field exists
    context = {'farmers': farmers}
    return render(request, "dashboard/farmer_list.html", context)

@login_required
def buyer_list(request):
    buyers= CustomUser.objects.filter(role='buyer')  # Assuming `user_type` field exists
    context = {'buyers': buyers}
    return render(request, "dashboard/buyer_list.html", context)

@login_required
def users_profile(request, user_id):  
    user = get_object_or_404(CustomUser, id=user_id) 

    if request.method == "POST":
        if 'is_activated' in request.POST:
            # Handle activation update
            is_activated = request.POST.get("is_activated")
            if is_activated == 'on':
                user.is_activated = True
            else:
                user.is_activated = False
            user.save()
            messages.success(request, "Account activation status updated successfully.")
            user = get_object_or_404(CustomUser, id=user_id) #Get the updated user object.
            return redirect('users_profile', user_id=user.id)

        elif 'first_name' in request.POST:
            user.first_name = request.POST.get("first_name")
            user.last_name = request.POST.get("last_name")
            user.region = request.POST.get("region")
            user.zone = request.POST.get("zone")
            user.phone = request.POST.get("phone")
            user.email = request.POST.get("email")
            user.save()

            messages.success(request, "Profile updated successfully!")
            return redirect('users_profile', user_id=user.id)
        
    return render(request, "dashboard/users-profile.html", {'user': user})


@login_required
def delete_user(request, user_id):
    if request.method == 'POST':
        # Only staff or superuser can delete others
        if not request.user.is_staff and not request.user.is_superuser:
            messages.error(request, "You don't have permission to delete users.")
            return redirect('admin_dashboard')
        
        user_to_delete = get_object_or_404(CustomUser, id=user_id)
        
        if user_to_delete == request.user:
            messages.error(request, "You cannot delete your own account from the admin panel.")
            return redirect('admin_dashboard')
        
        user_to_delete.delete()
        messages.success(request, f"User {user_to_delete.username} has been deleted.")
        return redirect('admin_dashboard')
    else:
        messages.error(request, "Invalid request.")
        return redirect('admin_dashboard')
    
@login_required
def products(request):
    sort_by = request.GET.get('sort', 'created_at') #default sort
    products = Product.objects.all().order_by(sort_by)

    context = {
        'products': products,
        'filter_title': 'All Products',
    }
    return render(request, 'dashboard/products.html', context)

@login_required
def cart_list(request): 
    sort_by = request.GET.get('sort', 'created_at') #default sort
    carts = Cart.objects.all().order_by(sort_by) #changed products to carts.

    context = {
        'carts': carts, #changed products to carts.
        'filter_title': 'All Carts', #or change according to filter.
    }
    return render(request, 'dashboard/cart.html', context)


@login_required
def paid_list(request): 
    sort_by = request.GET.get('sort', 'created_at') #default sort
    paids = Paid.objects.all().order_by(sort_by) #changed products to paids.

    context = {
        'paids': paids, #changed products to paids.
        'filter_title': 'All paids', #or change according to filter.
    }
    return render(request, 'dashboard/paid.html', context)


@login_required
def delete_cart_items(request):
    if request.method == "POST":
        data = json.loads(request.body)
        cart_ids = data.get("cart_ids", [])

        if not cart_ids:
            return JsonResponse({"success": False, "message": "No items selected for deletion."})

        Cart.objects.filter(id__in=cart_ids).delete()
        return JsonResponse({"success": True, "message": "Selected items have been successfully deleted."})


@login_required
def update_cart(request, cart_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cart = Cart.objects.get(id=cart_id)

            cart.order_quantity = data.get("order_quantity", cart.order_quantity)
            cart.order_price = data.get("order_price", cart.order_price)
            cart.order_category = data.get("order_category", cart.order_category)
            cart.save()

            return JsonResponse({"success": True, "message": "Cart item updated successfully."})
        except Cart.DoesNotExist:
            return JsonResponse({"success": False, "message": "Cart item not found."})

#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
