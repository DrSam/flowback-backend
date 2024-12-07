from flowback.group.models import Group
from flowback.user.models import User
from django.template.loader import render_to_string
from backend.settings import DEFAULT_FROM_EMAIL, SITE_URL
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
import jwt
from django.conf import settings


def email_verification_email(user_id):
    user = User.objects.get(id=user_id)
    data = {
        "email":user.email,
        "id":user.id
    }
    encoded_jwt = jwt.encode(data,settings.JWT_SECRET,algorithm='HS256')
    html_string = render_to_string(
        'user/verify_email.html',
        {
            'user':user,
            'site_url':SITE_URL,
            "token":encoded_jwt
        }
    )
    send_mail(
        'Please confirm your email',
        from_email=DEFAULT_FROM_EMAIL,
        message=strip_tags(html_string),
        html_message=html_string,
        recipient_list=[user.email]
    )





