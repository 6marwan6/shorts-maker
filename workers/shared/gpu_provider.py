"""GPU execution provider boundary (impl plan §1.12).

RATIFIED 2026-09-30 (owner decision G7): `gpu_dispatch` is the single application-facing GPU
execution boundary; `provider_job_id` is an OPAQUE provider-scoped id -- application code never
interprets it or branches on its format (local: the Celery dispatch task id; Modal: the Modal
call id). The method set submit/get_status/cancel is ratified. The dataclass field names remain
implementation-level; two additions made in Phase 3 are flagged for a one-line owner
ratification: `GPUJobStatus.outputs` (descriptors of objects the worker wrote to artifact
storage, replacing `output_artifact_ids` because the GPU worker does not write DB rows) and
`GPUJobStatus.failure_kind` (the §3.4 failure kind survives the JSON boundary).
RATIFIED 2026-10-02 (#7): output descriptors instead of output_artifact_ids; the worker reads
input metadata, executes, writes objects, returns descriptors/hashes/provider metadata, never
creates PostgreSQL artifact rows. One further addition (flagged): `submit(transport_inputs=...)`
carries descriptors of internal transport-envelope objects (the alignment task needs the ASR
envelope, which is deliberately not an artifact).

The provider knows nothing about ASR/diarization semantics; it runs a named task on artifact IDs.
Provider selection happens ONLY in `select_gpu_provider` (infrastructure layer) -- model
business logic never branches on environment (§1.12)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class GPUJobState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class GPUJobHandle:
    provider_job_id: str  # opaque; never parsed


@dataclass(frozen=True)
class GPUOutput:
    """Descriptor of an object the GPU worker wrote to storage (owner 2026-10-02 #7). The worker
    never writes DB rows. For Phase 3 this describes an internal transport envelope (NOT a
    canonical artifact, #6); the control plane records it in stage_runs.execution_metadata and
    materializes canonical artifacts (transcript_v1) itself."""
    kind: str  # e.g. "phase3_stage_output_v1" (transport envelope)
    stage: str
    schema_version: int
    storage_location: str
    checksum: str
    provenance: dict


@dataclass(frozen=True)
class GPUJobStatus:
    provider_job_id: str
    state: GPUJobState
    outputs: tuple[GPUOutput, ...] = ()
    error: str | None = None
    failure_kind: str | None = None  # a workers.shared.failures.FailureKind value


@dataclass(frozen=True)
class GPUCancelResult:
    provider_job_id: str
    cancelled: bool
    detail: str = ""


@dataclass(frozen=True)
class ConfigIdentity:
    config_version: str
    config_sha256: str


class GPUExecutionProvider(Protocol):
    async def submit(
        self, *, task_name: str, input_artifact_ids: tuple[str, ...], model_manifest: dict,
        config_identity: ConfigIdentity, request_id: str,
        transport_inputs: dict[str, dict] | None = None,
    ) -> GPUJobHandle: ...

    async def get_status(self, *, provider_job_id: str) -> GPUJobStatus: ...

    async def cancel(self, *, provider_job_id: str) -> GPUCancelResult: ...


GPU_TASK_NAME = "workers.gpu.execute_gpu_task"  # routed to the gpu_dispatch queue (celery_app.py)

_CELERY_STATE_MAP = {
    "PENDING": GPUJobState.PENDING, "RECEIVED": GPUJobState.PENDING,
    "STARTED": GPUJobState.RUNNING, "RETRY": GPUJobState.RUNNING,
    "SUCCESS": GPUJobState.SUCCEEDED, "FAILURE": GPUJobState.FAILED,
    "REVOKED": GPUJobState.CANCELLED,
}


@dataclass
class LocalROCmGPUProvider:
    """Enabled in D0/D1/D2 (RX 7800 XT, §1.12). Submission = a Celery task on the `gpu_dispatch`
    queue consumed by worker-gpu; provider_job_id is the Celery task id (owner G7: allowed, but
    opaque to callers). `celery_app` is injected by the infrastructure layer."""
    celery_app: object | None = None
    name: str = field(default="local_rocm", init=False)

    def _app(self):
        if self.celery_app is None:
            raise RuntimeError("LocalROCmGPUProvider requires an injected Celery app (infrastructure layer)")
        return self.celery_app

    async def submit(
        self, *, task_name: str, input_artifact_ids: tuple[str, ...], model_manifest: dict,
        config_identity: ConfigIdentity, request_id: str,
        transport_inputs: dict[str, dict] | None = None,
    ) -> GPUJobHandle:
        res = self._app().send_task(
            GPU_TASK_NAME,
            kwargs={
                "task_name": task_name, "input_artifact_ids": list(input_artifact_ids),
                "model_manifest": model_manifest,
                "config_version": config_identity.config_version,
                "config_sha256": config_identity.config_sha256, "request_id": request_id,
                "transport_inputs": transport_inputs or {},
            },
            task_id=request_id, queue="gpu_dispatch",
        )
        return GPUJobHandle(provider_job_id=res.id)

    async def get_status(self, *, provider_job_id: str) -> GPUJobStatus:
        ar = self._app().AsyncResult(provider_job_id)
        state = _CELERY_STATE_MAP.get(ar.state, GPUJobState.PENDING)
        if state is GPUJobState.SUCCEEDED:
            payload = ar.result or {}
            if payload.get("status") == "ok":
                outs = tuple(GPUOutput(**o) for o in payload.get("outputs", []))
                return GPUJobStatus(provider_job_id, GPUJobState.SUCCEEDED, outputs=outs)
            return GPUJobStatus(
                provider_job_id, GPUJobState.FAILED, error=payload.get("reason", "unknown"),
                failure_kind=payload.get("kind"))
        if state is GPUJobState.FAILED:
            return GPUJobStatus(provider_job_id, state, error=str(ar.result), failure_kind="TRANSIENT")
        return GPUJobStatus(provider_job_id, state)

    async def cancel(self, *, provider_job_id: str) -> GPUCancelResult:
        self._app().control.revoke(provider_job_id, terminate=False)
        return GPUCancelResult(provider_job_id, cancelled=True, detail="revoke requested")


_MODAL_NOTE = "ModalGPUProvider is wired at P0 (impl plan §1.16); never used in D0/D1/D2."


@dataclass
class ModalGPUProvider:
    """Enabled in P0 only (Modal L4, §1.12)."""
    name: str = field(default="modal", init=False)

    async def submit(self, **_): raise NotImplementedError(_MODAL_NOTE)
    async def get_status(self, **_): raise NotImplementedError(_MODAL_NOTE)
    async def cancel(self, **_): raise NotImplementedError(_MODAL_NOTE)


_PROVIDERS: dict[str, type] = {"local_rocm": LocalROCmGPUProvider, "modal": ModalGPUProvider}


def select_gpu_provider(name: str, **kwargs) -> GPUExecutionProvider:
    """Infrastructure/configuration layer only (§1.12)."""
    try:
        return _PROVIDERS[name](**kwargs)
    except KeyError:
        raise ValueError(f"unknown GPU provider {name!r}; allowed: {sorted(_PROVIDERS)}") from None
