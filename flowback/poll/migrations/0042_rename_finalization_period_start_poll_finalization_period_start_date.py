# Generated by Django 4.2.7 on 2024-05-24 09:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0041_alter_poll_approval_minimum_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='poll',
            old_name='finalization_period_start',
            new_name='finalization_period_start_date',
        ),
    ]
