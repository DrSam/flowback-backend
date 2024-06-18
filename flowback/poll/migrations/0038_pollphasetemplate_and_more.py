# Generated by Django 4.2.7 on 2024-06-17 12:54

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0032_group_blockchain_id'),
        ('poll', '0037_alter_pollpredictionbet_blockchain_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='PollPhaseTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('poll_type', models.IntegerField(choices=[(1, 'ranking'), (2, 'for_against'), (3, 'schedule'), (4, 'cardinal')])),
                ('poll_is_dynamic', models.BooleanField(default=False)),
                ('area_vote_time_delta', models.IntegerField(blank=True, null=True)),
                ('proposal_time_delta', models.IntegerField(blank=True, null=True)),
                ('prediction_statement_time_delta', models.IntegerField(blank=True, null=True)),
                ('prediction_bet_time_delta', models.IntegerField(blank=True, null=True)),
                ('delegate_vote_time_delta', models.IntegerField(blank=True, null=True)),
                ('vote_time_delta', models.IntegerField(blank=True, null=True)),
                ('end_time_delta', models.IntegerField()),
                ('created_by_group_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.groupuser')),
            ],
        ),
        migrations.AddConstraint(
            model_name='pollphasetemplate',
            constraint=models.CheckConstraint(check=models.Q(models.Q(models.Q(('poll_type', 4), ('poll_is_dynamic', False)), models.Q(models.Q(('area_vote_time_delta__isnull', False), ('proposal_time_delta__isnull', False), ('prediction_statement_time_delta__isnull', False), ('prediction_bet_time_delta__isnull', False), ('delegate_vote_time_delta__isnull', False), ('vote_time_delta__isnull', False), ('end_time_delta__isnull', False), _connector='OR'), _negated=True)), _negated=True), name='pollphasetemplatecardinalisvalid_check'),
        ),
        migrations.AddConstraint(
            model_name='pollphasetemplate',
            constraint=models.CheckConstraint(check=models.Q(models.Q(models.Q(('poll_type', 3), ('poll_is_dynamic', True), _connector='OR'), models.Q(('area_vote_time_delta__isnull', True), ('proposal_time_delta__isnull', True), ('prediction_statement_time_delta__isnull', True), ('prediction_bet_time_delta__isnull', True), ('delegate_vote_time_delta__isnull', True), ('vote_time_delta__isnull', False), ('end_time_delta__isnull', False), _connector='OR')), _negated=True), name='pollphasetemplatescheduleordynamicisvalid_check'),
        ),
    ]
