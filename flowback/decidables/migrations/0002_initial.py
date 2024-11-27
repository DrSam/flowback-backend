# Generated by Django 4.2.7 on 2024-11-27 11:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('group', '0001_initial'),
        ('decidables', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupuserdecidablevote',
            name='group_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_user_decidable_vote', to='group.groupuser'),
        ),
        migrations.AddField(
            model_name='groupuserdecidableoptionvote',
            name='group_decidable_option_access',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_user_decidable_option_vote', to='decidables.groupdecidableoptionaccess'),
        ),
        migrations.AddField(
            model_name='groupuserdecidableoptionvote',
            name='group_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_user_decidable_option_vote', to='group.groupuser'),
        ),
        migrations.AddField(
            model_name='groupdecidableoptionaccess',
            name='decidable_option',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_decidable_option_access', to='decidables.decidableoption'),
        ),
        migrations.AddField(
            model_name='groupdecidableoptionaccess',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_decidable_option_access', to='group.group'),
        ),
        migrations.AddField(
            model_name='groupdecidableoptionaccess',
            name='voters',
            field=models.ManyToManyField(through='decidables.GroupUserDecidableOptionVote', to='group.groupuser'),
        ),
        migrations.AddField(
            model_name='groupdecidableaccess',
            name='decidable',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_decidable_access', to='decidables.decidable'),
        ),
        migrations.AddField(
            model_name='groupdecidableaccess',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_decidable_access', to='group.group'),
        ),
        migrations.AddField(
            model_name='groupdecidableaccess',
            name='voters',
            field=models.ManyToManyField(through='decidables.GroupUserDecidableVote', to='group.groupuser'),
        ),
        migrations.AddField(
            model_name='decidableoption',
            name='decidable',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='child_options', to='decidables.decidable'),
        ),
        migrations.AddField(
            model_name='decidableoption',
            name='groups',
            field=models.ManyToManyField(related_name='decidable_options', through='decidables.GroupDecidableOptionAccess', to='group.group'),
        ),
        migrations.AddField(
            model_name='decidableoption',
            name='option',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decidable_option', to='decidables.option'),
        ),
        migrations.AddField(
            model_name='decidable',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='decidable', to='group.groupuser'),
        ),
        migrations.AddField(
            model_name='decidable',
            name='groups',
            field=models.ManyToManyField(related_name='decidables', through='decidables.GroupDecidableAccess', to='group.group'),
        ),
        migrations.AddField(
            model_name='decidable',
            name='parent_decidable',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_decidables', to='decidables.decidable'),
        ),
        migrations.AddField(
            model_name='decidable',
            name='parent_option',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_decidables', to='decidables.option'),
        ),
        migrations.AddField(
            model_name='decidable',
            name='primary_decidable',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='secondary_decidables', to='decidables.decidable'),
        ),
        migrations.AddField(
            model_name='decidable',
            name='root_decidable',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='descendent_decidables', to='decidables.decidable'),
        ),
        migrations.AddField(
            model_name='decidable',
            name='topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='decidables', to='group.topic'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='attachments', to='group.groupuser'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='decidable',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='decidables.decidable'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='option',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='decidables.option'),
        ),
    ]
