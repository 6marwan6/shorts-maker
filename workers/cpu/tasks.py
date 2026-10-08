"""CPU-queue task contracts (impl plan §1.6.1: worker-cpu owns deterministic media analysis,
discovery, qualification, Tier 1, edit planning, verification orchestration, hook/reframe CPU
work, Tier-2 CPU work). Phase 1 scope is the queue/task/idempotency CONTRACT only -- the actual
algorithms (discovery, qualification, DP edit planning, Layer 1/2 verification, ...) are Phases
5-11. Task bodies here intentionally raise NotImplementedError rather than faking a result, per
impl plan §13.4/§0: never invent behavior a later phase is responsible for.
"""
from __future__ import annotations

import asyncio

# Built lazily by whichever process imports this module (worker entrypoint or tests), never at
# import time with a hardcoded URL -- see workers/cpu/worker.py for the real entrypoint wiring.
celery_app = None


def bind(app) -> None:
    global celery_app
    celery_app = app

    @app.task(name="workers.cpu.normalize_source_video", bind=True, max_retries=3)
    def normalize_source_video(
        self, *, job_id: str, source_video_id: str, source_storage_key: str,
        source_artifact_id: str, max_duration_s: float,
    ):
        """impl plan Phase 2: NORMALIZING stage. Task ID at dispatch time must be
        `deterministic_task_id(job_id=..., stage_name="NORMALIZING", stage_input_sha256=...)`
        (§3.3); this body only executes the stage once dispatched."""
        from app.config import get_settings
        from app.db import dispose_engine, session_scope
        from app.models import Phase3DispatchIntent
        from app.storage import build_storage_adapter
        from shorts_config import load_config
        from sqlalchemy import select

        from workers.cpu.stage_normalize import run_normalization_stage
        from workers.shared import dispatch_intents
        from workers.shared.job_state import transition_job_state
        from workers.shared.stage_runner import ConfigIdentity

        settings = get_settings()
        source_storage = build_storage_adapter(settings, bucket_kind="source")
        artifact_storage = build_storage_adapter(settings, bucket_kind="artifacts")
        cfg = load_config()  # config@1 registry is the sole config-identity source (Phase 0 owner decision)
        config = ConfigIdentity(config_version=cfg.config_version, config_sha256=cfg.config_sha256)

        def _send(name: str, kwargs: dict, task_id: str, queue: str) -> None:
            self.app.send_task(name, kwargs=kwargs, task_id=task_id, queue=queue)

        async def _run():
            try:
                # ONE transaction (owner 2026-10-02 #9): normalized artifacts + media_manifest_v1 +
                # NORMALIZING->NORMALIZED + durable Phase-3 dispatch intent commit together, so a
                # crash can never leave a NORMALIZED job with no record that Phase 3 must run.
                async with session_scope() as session:
                    artifact_ids = await run_normalization_stage(
                        session, job_id=job_id, source_video_id=source_video_id,
                        source_storage_key=source_storage_key, source_artifact_id=source_artifact_id,
                        source_storage=source_storage, artifact_storage=artifact_storage,
                        config=config, max_duration_s=max_duration_s,
                    )
                    moved = await transition_job_state(
                        session, job_id=job_id, from_state="NORMALIZING", to_state="NORMALIZED")
                    if moved:
                        await dispatch_intents.create_intent(
                            session, job_id=job_id, source_video_id=source_video_id,
                            task_id=dispatch_intents.phase3_task_id(job_id, artifact_ids))
                    await session.commit()
                # Dispatch is a SEPARATE step after the atomic commit. If it fails or the process
                # dies here the intent stays PENDING and the reconciler resubmits it.
                if moved:
                    async with session_scope() as session:
                        intent = await session.scalar(select(Phase3DispatchIntent).where(
                            Phase3DispatchIntent.job_id == job_id))
                        await dispatch_intents.dispatch_intent(session, _send, intent)
                        await session.commit()
                return artifact_ids
            finally:
                await dispose_engine()  # no pooled asyncpg connection may outlive this asyncio.run() loop

        return asyncio.run(_run())

    @app.task(name="workers.cpu.run_transcript_preflight", bind=True, max_retries=3)
    def run_transcript_preflight(self, *, job_id: str, source_video_id: str):
        """impl plan Phase 3: ASR / language gate / forced alignment / diarization / sentence
        segmentation while the job stays NORMALIZED (owner decision C2)."""
        from datetime import UTC, datetime

        from app.config import get_settings
        from app.db import dispose_engine, session_scope
        from app.storage import build_storage_adapter
        from shorts_config import load_config

        from workers.cpu.language_gate import FastTextLanguageID
        from workers.cpu.stage_transcript import Phase3Deps, run_phase3
        from workers.shared import dispatch_intents
        from workers.shared.gpu_provider import select_gpu_provider

        settings = get_settings()
        cfg = load_config()
        storage = build_storage_adapter(settings, bucket_kind="artifacts")
        gpu = select_gpu_provider("local_rocm", celery_app=self.app)  # D0/D1/D2; P0 = "modal" (config layer)

        async def _run():
            try:
                async with session_scope() as session:
                    last_beat = [datetime.now(UTC)]

                    async def beat() -> None:  # lease heartbeat, own short transaction, throttled
                        now = datetime.now(UTC)
                        if (now - last_beat[0]).total_seconds() < dispatch_intents.HEARTBEAT_MIN_INTERVAL_S:
                            return
                        last_beat[0] = now
                        async with session_scope() as hb:
                            await dispatch_intents.heartbeat(hb, job_id=job_id, now=now)
                            await hb.commit()

                    deps = Phase3Deps(
                        session=session, cfg=cfg, artifact_storage=storage, gpu=gpu, heartbeat=beat,
                        language_backend_factory=lambda: FastTextLanguageID.from_provisioned_artifact(
                            cfg["LANGUAGE_ID_MODEL_ID"]))
                    tid = await run_phase3(deps, job_id=job_id, source_video_id=source_video_id)
                    await session.commit()
                    return tid
            finally:
                await dispose_engine()

        return asyncio.run(_run())

    @app.task(name="workers.cpu.reverify_user_edit", bind=True, max_retries=3)
    def reverify_user_edit(self, *, short_candidate_id: str, edit_plan_id: str):
        """impl plan Phase 12: DISPLAYED -> USER_EDITING -> REVERIFYING -> DISPLAYED|BLOCKED_USER_EDIT.
        Real body (safe-boundary snap, Layer 1, Layer 2 when applicable) lands in Phase 7/8."""
        raise NotImplementedError(
            "edit-plan verification is implemented in Phase 7 (edit planning) and Phase 8 "
            "(Layer 1 / Layer 2 verification) -- Phase 1 only provides this task's queue "
            "routing and idempotency contract (impl plan §1.6.1, §3.2)."
        )

    @app.task(name="workers.cpu.refresh_reframe_only", bind=True, max_retries=3)
    def refresh_reframe_only(self, *, short_candidate_id: str, strategy: str):
        """impl plan §2.26.1: reframe-only edits create a new reframe lineage and skip content
        verification. Real body lands in Phase 10 (reframe planning)."""
        raise NotImplementedError(
            "reframe planning is implemented in Phase 10 -- Phase 1 only provides this task's "
            "queue routing and idempotency contract."
        )

    @app.task(name="workers.maintenance.reconcile_phase3_dispatch", bind=True)
    def reconcile_phase3_dispatch(self):
        """Periodic (celery beat, `maintenance` queue; owner 2026-10-02 #9). Resubmits pending /
        lease-expired Phase-3 dispatch intents and creates the intent for NORMALIZED jobs that
        have none. Safe to run concurrently with itself and with live Phase-3 tasks."""
        from app.db import dispose_engine, session_scope

        from workers.shared import dispatch_intents

        def _send(name: str, kwargs: dict, task_id: str, queue: str) -> None:
            self.app.send_task(name, kwargs=kwargs, task_id=task_id, queue=queue)

        async def _run():
            try:
                async with session_scope() as session:
                    rep = await dispatch_intents.reconcile(session, _send)
                    await session.commit()
                    return rep.__dict__
            finally:
                await dispose_engine()

        return asyncio.run(_run())

    @app.task(name="workers.maintenance.sweep_transport_objects", bind=True)
    def sweep_transport_objects(self):
        """Periodic (beat, `maintenance` queue; owner 2026-10-04 #7): safe, idempotent deletion of
        internal transport-envelope objects per the retention policy. Never touches canonical
        artifacts; a failure is recorded on the registry row."""
        from app.config import get_settings
        from app.db import dispose_engine, session_scope
        from app.storage import build_storage_adapter

        from workers.shared import transport_retention

        storage = build_storage_adapter(get_settings(), bucket_kind="artifacts")

        async def _run():
            try:
                async with session_scope() as session:
                    rep = await transport_retention.sweep(session, storage)
                    await session.commit()
                    return rep.__dict__
            finally:
                await dispose_engine()

        return asyncio.run(_run())

    return (normalize_source_video, run_transcript_preflight, reconcile_phase3_dispatch,
            sweep_transport_objects, reverify_user_edit, refresh_reframe_only)
