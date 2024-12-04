# Generated by Django 4.2.7 on 2024-11-27 11:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('chat', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='messagefilecollection',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='messagechanneltopic',
            name='channel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.messagechannel'),
        ),
        migrations.AddField(
            model_name='messagechannelparticipant',
            name='channel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.messagechannel'),
        ),
        migrations.AddField(
            model_name='messagechannelparticipant',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='attachments',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='chat.messagefilecollection'),
        ),
        migrations.AddField(
            model_name='message',
            name='channel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.messagechannel'),
        ),
        migrations.AddField(
            model_name='message',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='message_parent', to='chat.message'),
        ),
        migrations.AddField(
            model_name='message',
            name='topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chat.messagechanneltopic'),
        ),
        migrations.AddField(
            model_name='message',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='messagechannelparticipant',
            unique_together={('user', 'channel')},
        ),
    ]