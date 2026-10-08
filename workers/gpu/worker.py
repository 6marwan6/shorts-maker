"""Entrypoint for `celery -A workers.gpu.worker worker -Q gpu_dispatch` (impl plan §1.4/§1.6.2)."""
from __future__ import annotations

import os

from workers.gpu import tasks
from workers.shared.celery_app import make_celery_app

app = make_celery_app(os.environ.get("SHORTS_MAKER_REDIS_URL", "redis://127.0.0.1:6379/0"))
tasks.bind(app)
