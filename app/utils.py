import os
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.auth import get_user_model
import csv
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings

def is_email_valid(email):
    csv_file_path = os.path.join(settings.BASE_DIR, 'app', 'data', 'emails.csv')
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['email'] == email:
                return True
    return False


def create_user_from_csv(email, request):
    User = get_user_model()
    csv_file_path = os.path.join(settings.BASE_DIR, 'app', 'data', 'emails.csv')

    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['email'] == email:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                )
                user.is_active = False
                user.save()

                activation_link = generate_activation_link(user, request)
                send_activation_email(user, activation_link)
                
                return user

    return None






from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

def generate_activation_link(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    activation_link = request.build_absolute_uri(
        reverse('activate', kwargs={'uidb64': uid, 'token': token})
    )
    return activation_link



from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_activation_email(user, activation_link):
    subject = 'Activate Your Account'
    html_message = render_to_string('registration/activation_email.html', {
        'activation_link': activation_link,
        'user': user,
    })
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, 'atsewkaleb@gmail.com', [user.email], html_message=html_message)

