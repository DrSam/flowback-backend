# Generated by Django 4.0.8 on 2022-12-07 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0006_alter_grouppermissions_allow_vote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grouppermissions',
            name='create_poll',
            field=models.BooleanField(default=True),
        ),
    ]