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
        f'{user.first_name} wants to share a community with you',
        from_email=DEFAULT_FROM_EMAIL,
        message=strip_tags(html_string),
        html_message=html_string,
        recipient_list=[user.email]
    )





