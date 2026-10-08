"""The API process enqueues tasks by name only (impl plan §1.6.1: worker-cpu owns the actual
media/ml-dependent task bodies; apps/api must not need those dependency groups). This is a
thin `send_task` client sharing the same broker URL and queue-routing config as
workers/shared/celery_app.py -- never a second, drifting queue-name definition.
"""
from __future__ import annotations

from celery import Celery

from workers import make_celery_app


def get_task_client(redis_url: str) -> Celery:
    return make_celery_app(redis_url)
