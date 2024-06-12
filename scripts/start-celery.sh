#!/bin/sh
 
# For the 'worker' process
celery -A backend worker --loglevel=info & \

# For the 'beat scheduler'
celery -A backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler