# Generated by Django 4.2.7 on 2024-05-31 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("poll", "0039_poll_finalization_period_start"),
    ]

    operations = [
        migrations.AddField(
            model_name="pollproposal",
            name="proposal_votes_info",
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
