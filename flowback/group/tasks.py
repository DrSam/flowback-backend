from flowback.group.models import Group
from flowback.user.models import User
from django.template.loader import render_to_string
from backend.settings import DEFAULT_FROM_EMAIL, SITE_URL
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives

def share_group_with_user(group_id,user_id,request_user_id):
    group = Group.objects.get(id=group_id)
    user = User.objects.get(id=user_id)
    request_user = User.objects.get(id=request_user_id)
    html_string = render_to_string(
        'group/share_group.html',
        {
            'group':group,
            'user':user,
            'request_user':request_user,
            'site_url':SITE_URL
        }
    )
    send_mail(
        f'{request_user.first_name} wants to share a community with you',
        from_email=DEFAULT_FROM_EMAIL,
        message=strip_tags(html_string),
        html_message=html_string,
        recipient_list=[user.email]
    )


def share_group_with_email(group_id,email,request_user_id):
    group = Group.objects.get(id=group_id)
    request_user = User.objects.get(id=request_user_id)
    user = {
        'first_name':email
    }
    html_string = render_to_string(
        'group/share_group.html',
        {
            'group':group,
            'user':user,
            'request_user':request_user,
            'site_url':SITE_URL
        }
    )
    send_mail(
        f'{request_user.first_name} wants to share a community with you',
        from_email=DEFAULT_FROM_EMAIL,
        message=strip_tags(html_string),
        html_message=html_string,
        recipient_list=[email]
    )

def invite_user_to_group(group_id,user_id,request_user_id):
    group = Group.objects.get(id=group_id)
    user = User.objects.get(id=user_id)
    request_user = User.objects.get(id=request_user_id)
    html_string = render_to_string(
        'group/invite_user.html',
        {
            'group':group,
            'user':user,
            'request_user':request_user,
            'site_url':SITE_URL
        }
    )
    send_mail(
        f'{request_user.first_name} invited you to join {group.name}',
        from_email=DEFAULT_FROM_EMAIL,
        message=strip_tags(html_string),
        html_message=html_string,
        recipient_list=[user.email]
    )


def invite_email_to_group(group_id,email,request_user_id):
    group = Group.objects.get(id=group_id)
    request_user = User.objects.get(id=request_user_id)
    user = {
        'first_name':email
    }
    html_string = render_to_string(
        'group/invite_user.html',
        {
            'group':group,
            'user':user,
            'request_user':request_user,
            'site_url':SITE_URL
        }
    )
    send_mail(
        f'{request_user.first_name} invited you to join {group.name}',
        from_email=DEFAULT_FROM_EMAIL,
        message=strip_tags(html_string),
        html_message=html_string,
        recipient_list=[email]
    )
