# Generated by Django 4.2.7 on 2024-09-08 17:33

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0037_group_default_approval_minimum_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='default_quorum',
            field=models.IntegerField(default=50, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)]),
        ),
    ]
