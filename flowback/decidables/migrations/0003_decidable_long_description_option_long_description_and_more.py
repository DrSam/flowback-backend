# Generated by Django 4.2.7 on 2024-12-17 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('decidables', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='decidable',
            name='long_description',
            field=models.CharField(blank=True, default='', max_length=1600),
        ),
        migrations.AddField(
            model_name='option',
            name='long_description',
            field=models.CharField(blank=True, default='', max_length=1600),
        ),
        migrations.AlterField(
            model_name='decidable',
            name='description',
            field=models.CharField(blank=True, default='', max_length=240),
        ),
        migrations.AlterField(
            model_name='option',
            name='description',
            field=models.CharField(blank=True, default='', max_length=240),
        ),
    ]