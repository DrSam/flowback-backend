# Generated by Django 4.2.7 on 2024-05-24 07:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0002_filesegment_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='filecollection',
            options={'ordering': ['created_at']},
        ),
        migrations.AlterModelOptions(
            name='filesegment',
            options={'ordering': ['created_at']},
        ),
    ]