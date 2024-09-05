from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_sharing.settings')

app = Celery('expense_sharing')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send_weekly_summaries': {
        'task': 'expenses.tasks.send_weekly_summaries',
        'schedule': crontab(hour=0, minute=0, day_of_week='monday'),
    },
}

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
