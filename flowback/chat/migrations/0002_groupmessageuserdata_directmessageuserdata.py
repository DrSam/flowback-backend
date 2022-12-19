# Generated by Django 4.0.8 on 2022-12-07 19:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0006_alter_grouppermissions_allow_vote'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupMessageUserData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('timestamp', models.DateTimeField()),
                ('group_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='group.groupuser')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DirectMessageUserData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('timestamp', models.DateTimeField()),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='directmessageuserdata_target', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='directmessageuserdata_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'target', 'timestamp')},
            },
        ),
    ]
