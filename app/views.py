from urllib import response
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Request, Cart
from .forms import ReqeustEditClient, ReqeustEditStaff, RequestEditForm, RequestForm, UserRegistrationForm, ProductForm
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import update_session_auth_hash
import requests
from django.http import JsonResponse
from .models import Paid
from django.conf import settings
import json
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from app.models import CustomUser
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.timezone import now
from datetime import timedelta
from .models import Log




def home_view(request):
    if request.user.is_authenticated:
        logout(request)
        return render(request, 'home.html')
    else:
        # User is not logged in
        return render(request, 'home.html') #Or redirect to login page.


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
    return redirect('request_list')



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
            product.save()
            messages.success(request, "Product created successfully.")
            # Log the product creation
            Log.objects.create(
                message=f"Farmer {request.user.username} added product: {product.product_name}",
                log_type="success"
            )
            return redirect('product_list')  # Redirect to your product list view or any other page
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm()
    
    return render(request, 'farmer/add_product.html', {'form': form})


@login_required
def product_detail(request, product_id):
    # Use the GET parameter "selected" if provided; otherwise, fallback to the URL parameter.
    selected_product_id = request.GET.get('selected', product_id)
    product = get_object_or_404(Product, id=selected_product_id)
    # Log the product detail view
    Log.objects.create(
        message=f"Buyer {request.user.username} viewed product details: {product.product_name}",
        log_type="info"  # Or another appropriate log type
    )
    context = { 'selected_product': product }
    return render(request, 'buyer/product_detail.html', context)


#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
# Cart adding-----------------------------------------------------------------------------------------------------------------
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
        
        # Calculate total price; using Decimal for arithmetic accuracy.
        try:
            price_per_kg = Decimal(product.product_price)
        except Exception:
            price_per_kg = Decimal('0.00')
        total_price = Decimal(quantity) * price_per_kg
        
        # Copy key fields from the product to the cart record.
        # Adjust the field names as per your Product model.
        order_name = product.product_name  
        order_price = price_per_kg  
        order_image = product.product_image  
        order_category = product.product_category
        created_at = product.created_at
        
        # Update product quantity and create cart record atomically
        with transaction.atomic():
            remaining_quantity = int(product.product_quantity) - quantity
            
            # Create the Cart record with copied product data.
            Cart.objects.create(
                order_name=order_name,
                order_quantity=Decimal(quantity),
                order_price=order_price,
                order_image=order_image,
                order_category=order_category,
                total_price=total_price,
                farmer=product.farmer,
                buyer=request.user,
                created_at=created_at,
            )
            
            # If remaining quantity is 0, delete the product;
            # otherwise, update its quantity.
            if remaining_quantity == 0:
                product.delete()
            else:
                product.product_quantity = str(remaining_quantity)
                product.save()
        
        messages.success(request, "Product added to cart successfully!")
        # Log the add to cart action
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

def payment_detail(request, item_id):
    # Fetch the item from the database using the passed item_id
    item = get_object_or_404((Cart), id=item_id)

    # Pass the item to the template for rendering
    return render(request, 'buyer/payment_detail.html', {'item': item})


CHAPA_SECRET_KEY = "CHASECK_TEST-VPikVFcVYY4wTq4MRgonDUZujkWctaH9"


def chapa_callback(request, item_id):
    # Get transaction details from the Chapa callback
    trx_ref = request.GET.get("trx_ref")
    status = request.GET.get("status")

    print(f"Received callback - trx_ref: {trx_ref}, status: {status}")

    if not trx_ref:
        return JsonResponse({"error": "Missing transaction reference"}, status=400)

    # Verify the transaction with Chapa
    verification_url = f"https://api.chapa.co/v1/transaction/verify/{trx_ref}"
    headers = {"Authorization": f"Bearer {CHAPA_SECRET_KEY}"}

    response = requests.get(verification_url, headers=headers)

    print(f"Chapa verification response: {response.status_code}, {response.text}")

    if response.status_code == 200:
        data = response.json()
        payment_data = data.get("data", {})

        # Check if the payment was successful
        if data.get("status") == "success":
            print(f"✅ Payment verified for trx_ref: {trx_ref}")

            # Get the Cart item based on the item_id passed in the URL
            cart_item = get_object_or_404(Cart, id=item_id)

            # Get items_with_ref from request (but it's not really used)
            items_with_ref = json.loads(request.POST.get('items_with_ref', '[]'))

            # Store payment data in Paid model
            paid_item = Paid.objects.create(
                paid_product_name=cart_item.order_name,  
                paid_product_quantity=cart_item.order_quantity,  
                paid_product_price=cart_item.order_price,  
                paid_product_image=cart_item.order_image,  
                paid_product_category=cart_item.order_category,  
                total_price=cart_item.total_price,
                created_at=cart_item.created_at, 
                farmer=cart_item.farmer,  
                buyer=cart_item.buyer,  
                transaction_reference=trx_ref,  # ✅ FIXED: Use `trx_ref` instead of `tx_ref`
                payment_status='success',  
            )

            # ✅ Optional: Remove the cart item after successful payment
            cart_item.delete()

            return JsonResponse({"message": "Payment verified successfully"})
        else:
            print(f"❌ Payment verification failed: {data}")
            return JsonResponse({"error": "Payment verification failed"}, status=400)
    else:
        print(f"⚠️ Chapa verification request failed for trx_ref: {trx_ref}")
        return JsonResponse({"error": "Chapa verification request failed"}, status=400)



def chapa_return(request):
    return render(request, "buyer/payment_result.html")


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
    total_product_value = Product.objects.annotate(
        total_value=ExpressionWrapper(F('product_quantity') * F('product_price'), output_field=DecimalField())
    ).aggregate(total_value_sum=Sum('total_value'))['total_value_sum'] or 0
    total_cart_value = Cart.objects.aggregate(
        cart_total_value_sum=Sum(F('order_quantity') * F('order_price'))
    )['cart_total_value_sum'] or 0
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
        'product_count_month': product_count_month,
        'cart_count_month': cart_count_month,
        'product_count_day': product_count_day,
        'cart_count_day': cart_count_day,
        'product_count_24_hours': product_count_24_hours,
        'cart_count_24_hours': cart_count_24_hours,
        'total_product_value': total_product_value,
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
            user.location = request.POST.get("location")
            user.phone = request.POST.get("phone")
            user.email = request.POST.get("email")
            user.bank_name = request.POST.get("bank_name")
            user.bank_number = request.POST.get("bank_number")
            user.save()

            messages.success(request, "Profile updated successfully!")
            return redirect('users_profile', user_id=user.id)
        
    return render(request, "dashboard/users-profile.html", {'user': user})


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

# request creation
@login_required
def create_request(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            request_instance = form.save(commit=False)
            request_instance.requester_email = request.user.email
            request_instance.requester_name = request.user.first_name
            request_instance.request_location = request.user.location
            request_instance.request_department = request.user.department
            request_instance.requester_phone = request.user.phone
            request_instance = form.save()
            return redirect('view_request', pk=request_instance.pk)
    else:
        form = RequestForm()
    return render(request, 'requests/create_request.html', {'form': form})

@login_required
def view_request(request, pk):
    request_instance = get_object_or_404(Request, pk=pk)
    return render(request, 'requests/view_request.html', {'request_instance': request_instance})

@login_required
def request_list(request):
    user = request.user
    if user.role == 'team_leader':
        requests = Request.objects.filter(assigned_team_leader=user)
    elif user.role == 'staff':
        requests = Request.objects.filter(assigned_staff=user)
    elif user.role == 'client':
        requests = Request.objects.filter(requester_email=user.email)
    elif user.role == 'ict_director':
        requests = Request.objects.all()
    else:
        requests = Request.objects.none()
        
    return render(request, 'requests/request_list.html', {'requests': requests})

@login_required
def edit_request(request, pk):
    user = request.user
    request_instance = get_object_or_404(Request, pk=pk)
    if request.method == 'POST':
        if user.role == 'client':
            form = ReqeustEditClient(request.POST, instance=request_instance)
        elif user.role == 'staff':
            form = ReqeustEditStaff(request.POST, instance=request_instance)
        else :
            form = RequestEditForm(request.POST, instance=request_instance)
        if form.is_valid():
            form.save()
            return redirect('view_request', pk=request_instance.pk)
    else:
        if user.role == 'client':
            form = ReqeustEditClient(instance=request_instance)
        elif user.role == 'staff':
            form = ReqeustEditStaff(instance=request_instance)
        else :
            form = RequestEditForm(instance=request_instance)
    return render(request, 'requests/edit_request.html', {'form': form, 'request_instance': request_instance})
