# Generated by Django 4.2.7 on 2024-05-24 07:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0005_alter_kanbanentry_description'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='kanbanentry',
            options={'ordering': ['created_at']},
        ),
    ]