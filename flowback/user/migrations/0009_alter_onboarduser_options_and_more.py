# Generated by Django 4.2.7 on 2024-05-24 07:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_user_configuration'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='onboarduser',
            options={'ordering': ['created_at']},
        ),
        migrations.AlterModelOptions(
            name='passwordreset',
            options={'ordering': ['created_at']},
        ),
    ]