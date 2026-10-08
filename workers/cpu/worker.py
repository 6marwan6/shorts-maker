"""Entrypoint for `celery -A workers.cpu.worker worker -Q cpu,maintenance --beat` (impl plan §1.4 queue placement).
worker-cpu is also where Celery Beat runs embedded in D0/D1/D2 (impl plan §1.6.1)."""
from __future__ import annotations

import os

from workers.cpu import tasks
from workers.shared.celery_app import make_celery_app

# Owner 2026-10-04 #2: worker-cpu consumes BOTH queues; embedded Beat keeps scheduling reconciliation
# and the transport-retention sweep. No additional deployed service.
WORKER_QUEUES = ("cpu", "maintenance")
WORKER_COMMAND = f"celery -A workers.cpu.worker worker -Q {','.join(WORKER_QUEUES)} --beat --loglevel=info"

REDIS_URL = os.environ.get("SHORTS_MAKER_REDIS_URL", "redis://127.0.0.1:6379/0")

app = make_celery_app(REDIS_URL)
tasks.bind(app)
