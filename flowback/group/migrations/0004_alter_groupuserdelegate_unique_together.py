# Generated by Django 4.0.3 on 2022-08-25 12:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0003_groupuserinvite_external'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='groupuserdelegate',
            unique_together={('delegator', 'delegate', 'group')},
        ),
    ]