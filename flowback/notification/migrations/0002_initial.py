# Generated by Django 4.2.7 on 2024-11-27 11:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('notification', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationsubscription',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='notificationobject',
            name='channel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notification.notificationchannel'),
        ),
        migrations.AlterUniqueTogether(
            name='notificationchannel',
            unique_together={('category', 'sender_type', 'sender_id')},
        ),
        migrations.AddField(
            model_name='notification',
            name='notification_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notification.notificationobject'),
        ),
        migrations.AddField(
            model_name='notification',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='notificationsubscription',
            unique_together={('user', 'channel')},
        ),
        migrations.AlterUniqueTogether(
            name='notification',
            unique_together={('user', 'notification_object')},
        ),
    ]