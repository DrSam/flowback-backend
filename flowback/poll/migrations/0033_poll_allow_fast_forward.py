# Generated by Django 4.2.7 on 2024-04-21 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0032_pollproposaltypeschedule_unique_proposaltypeschedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='allow_fast_forward',
            field=models.BooleanField(default=False),
        ),
    ]