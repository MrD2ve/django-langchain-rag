import os
from celery import Celery

# Installing the default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# We use a configuration string so that the worker does not have to
# serialize the configuration object when running on Windows/Linux.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically find tasks (tasks.py) in registered applications (INSTALLED_APPS)
app.autodiscover_tasks()