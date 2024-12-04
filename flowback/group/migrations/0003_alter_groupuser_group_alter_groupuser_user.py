# Generated by Django 4.2.7 on 2024-12-04 05:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('group', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupuser',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_users', to='group.group'),
        ),
        migrations.AlterField(
            model_name='groupuser',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_users', to=settings.AUTH_USER_MODEL),
        ),
    ]
