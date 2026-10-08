"""Celery app + the 6 fixed queues (impl plan §1.4). Queue *names* never change between
deployment modes (impl plan §1.16 'What changes at each promotion'); only where each queue's
workers run does.

    io            -> upload verification, artifact I/O, metadata fetch
    cpu           -> normalization, analysis, discovery, qualification, Tier 1, edit planning,
                      verification orchestration, ranking
    llm           -> Kimi K3 / DeepSeek V4 Pro runtime calls
    gpu_dispatch  -> invoke/wait for the configured GPU execution provider
    render        -> FFmpeg render jobs
    maintenance   -> cleanup, metric collection, scheduled evaluations

No stage executes synchronously inside an HTTP request except request validation,
authorization and job-record creation (impl plan §1.4) -- apps/api routers only enqueue tasks
by name; they never import worker task bodies directly, so the API process never needs the
`media`/`ml` dependency groups.
"""
from __future__ import annotations

from app.config import get_settings
from celery import Celery

QUEUES = ("io", "cpu", "llm", "gpu_dispatch", "render", "maintenance")


def make_celery_app(redis_url: str) -> Celery:
    app = Celery("shorts_maker", broker=redis_url, backend=redis_url)
    app.conf.update(
        task_default_queue="cpu",
        task_queues=None,  # queues are selected per-task via task_routes; no fixed exchange topology needed for MVP
        task_routes={
            "workers.cpu.*": {"queue": "cpu"},
            "workers.io.*": {"queue": "io"},
            "workers.llm.*": {"queue": "llm"},
            "workers.gpu.*": {"queue": "gpu_dispatch"},
            "workers.render.*": {"queue": "render"},
            "workers.maintenance.*": {"queue": "maintenance"},
        },
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        # Owner 2026-10-02 #9 / 2026-10-04 #2,#7: durable Phase-3 dispatch reconciler and transport-
        # object retention sweep. Beat runs embedded in worker-cpu (impl plan §1.4), which consumes
        # BOTH `cpu` and `maintenance`. Intervals are operational Settings, not config@1.
        beat_schedule={
            "reconcile-phase3-dispatch": {
                "task": "workers.maintenance.reconcile_phase3_dispatch",
                "schedule": float(get_settings().reconcile_interval_s),
                "options": {"queue": "maintenance"},
            },
            "sweep-transport-objects": {
                "task": "workers.maintenance.sweep_transport_objects",
                "schedule": float(get_settings().transport_sweep_interval_s),
                "options": {"queue": "maintenance"},
            },
        },
    )
    return app
