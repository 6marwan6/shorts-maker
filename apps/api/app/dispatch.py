"""API-side stage dispatch (impl plan §1.6.1: "apps/api routers only enqueue tasks by name;
they never import worker task bodies directly, so the API process never needs the media/ml
dependency groups"). This module sends Celery tasks by name via `send_task`; it must never
`import workers.cpu.tasks` (or `workers.gpu.*` / `workers.render.*`).

Deliberately separate from job-row creation (owner correction, this session): the CREATED
commit and the NORMALIZING dispatch/transition are two independent steps, not one DB
transaction spanning the queue, to avoid the classic DB/queue atomicity problem. If dispatch
fails after CREATED is committed, the job is left in CREATED with no running stage -- a
full crash-recovery/outbox sweep is a Phase 18 reliability concern (§18.2 "job resume from
last successful artifact"), not solved here.
"""
from __future__ import annotations

from celery import Celery

from .config import Settings

_celery_client: Celery | None = None


def get_celery_client(settings: Settings) -> Celery:
    """A thin producer-only client: never binds task bodies (no `tasks.bind(app)` call here)."""
    global _celery_client
    if _celery_client is None:
        _celery_client = Celery("shorts_maker_api", broker=settings.redis_url, backend=settings.redis_url)
        _celery_client.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")
    return _celery_client


def dispatch_normalize_source_video(
    settings: Settings, *, job_id: str, source_video_id: str, source_storage_key: str,
    source_artifact_id: str, stage_input_sha256: str, max_duration_s: float,
) -> str:
    # workers.shared is a dependency-light boundary module (shorts_config + sqlalchemy + app.models
    # only) -- it is NOT a task body, so importing it here does not violate §1.6.1's "never import
    # worker task bodies directly" (that rule targets workers.cpu.tasks / .gpu / .render, which
    # pull in ffmpeg/whisperx/torch). One canonical deterministic_task_id, used by both sides.
    from workers.shared.stage_runner import deterministic_task_id

    client = get_celery_client(settings)
    task_id = deterministic_task_id(
        job_id=job_id, stage_name="NORMALIZING", stage_input_sha256=stage_input_sha256)
    client.send_task(
        "workers.cpu.normalize_source_video",
        kwargs={
            "job_id": job_id, "source_video_id": source_video_id,
            "source_storage_key": source_storage_key, "source_artifact_id": source_artifact_id,
            "max_duration_s": max_duration_s,
        },
        task_id=task_id, queue="cpu",
    )
    return task_id
