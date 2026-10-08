"""GPU-queue task contract (owner G7). Routed to `gpu_dispatch` by workers.shared.celery_app."""
from __future__ import annotations

import asyncio

celery_app = None


def bind(app, *, backends_factory=None) -> None:
    global celery_app
    celery_app = app

    @app.task(name="workers.gpu.execute_gpu_task", bind=True)
    def execute_gpu_task(
        self, *, task_name: str, input_artifact_ids: list[str], model_manifest: dict,
        config_version: str, config_sha256: str, request_id: str,
        transport_inputs: dict | None = None,
    ):
        from app.config import get_settings
        from app.db import session_scope
        from app.storage import build_storage_adapter
        from shorts_config import load_config

        from workers.gpu.backends import default_backends
        from workers.gpu.execute import run_gpu_task
        from workers.shared.failures import BlockedBySpec

        cfg = load_config()
        if cfg.config_sha256 != config_sha256:
            return {"status": "error", "kind": "PERMANENT_VALIDATION", "reason": "config_identity_mismatch"}
        try:
            backends = (backends_factory or default_backends)(cfg)
        except BlockedBySpec as exc:
            return {"status": "error", "kind": "BLOCKED_BY_DEPENDENCY", "reason": str(exc)[:500]}
        storage = build_storage_adapter(get_settings(), bucket_kind="artifacts")

        async def _run():
            async with session_scope() as session:
                return await run_gpu_task(
                    session, task_name=task_name, input_artifact_ids=input_artifact_ids, cfg=cfg,
                    backends=backends, artifact_storage=storage,
                    transport_inputs=transport_inputs)

        return asyncio.run(_run())

    return execute_gpu_task
