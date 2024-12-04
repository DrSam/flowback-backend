# Generated by Django 4.2.7 on 2024-12-04 05:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feed', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_edited',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='message',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='quote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quoted_by', to='feed.message'),
        ),
        migrations.AddField(
            model_name='message',
            name='uuid',
            field=models.CharField(blank=True, default='', max_length=16),
        ),
    ]