import os

from celery import Celery

import jopify.celeryconfig as celeryconfig


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jopify.settings')
app = Celery("job_scraper")
app.config_from_object(celeryconfig)

app.autodiscover_tasks()

