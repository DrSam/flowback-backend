# Generated by Django 4.2.7 on 2024-06-28 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll', '0044_merge_20240618_1551'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pollphasetemplate',
            name='poll_type',
            field=models.IntegerField(choices=[(1, 'ranking'), (2, 'for_against'), (3, 'schedule'), (4, 'cardinal'), (1001, 'vote')]),
        ),
    ]