from django.core.management.base import BaseCommand
from django_q.models import Schedule
from datetime import datetime
import pytz
from django.utils import timezone

class Command(BaseCommand):
    help = 'Ensure a scheduled task is running for calculating decidable results'

    def handle(self, *args, **kwargs):
        schedule = Schedule.objects.filter(
            name='decidable results'
        ).first()
        if schedule:
            return
        schedule = Schedule.objects.create(
            func='flowback.decidables.tasks.compute_voting_results',
            name='decidable results',
            schedule_type=Schedule.MINUTES,
            minutes=5,
            repeats=-1
        )