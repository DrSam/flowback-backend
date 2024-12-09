from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from flowback.user.models import User
from flowback.user.models import OnboardUser
from django import forms

admin.site.register(OnboardUser)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'is_staff')
    list_filter = ('is_staff',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name','last_name','country','zip','birth_date','profile_image', 'banner_image', 'bio', 'website','email_confirmed')}),
        ('Permissions', {'fields': ('is_staff',)}),
        ('Activity', {'fields': ('last_login',)}),
        ('Notifications', {'fields': ('email_notifications',)}),
        ('Blocked Users',{'fields':('blocked_users',)}),
        ('Language',{'fields':('language',)})
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request,obj,**kwargs)
        form.base_fields['blocked_users'].required = False
        return form
