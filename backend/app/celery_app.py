"""
Celery application configuration for async task processing.

This module sets up Celery with Redis as the message broker and result backend
for handling long-running optimization tasks asynchronously.
"""

from celery import Celery
import os

# Get Redis URL from environment or use default
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Create Celery app
celery_app = Celery(
    'smart_scheduling',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.optimization_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=86400,  # Results expire after 24 hours
)
