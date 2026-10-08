from __future__ import annotations

from fastapi import FastAPI

from .routers import auth, candidates, jobs, uploads

app = FastAPI(title="shorts-maker API", version="0.1.0")

app.include_router(auth.router)
app.include_router(auth.me_router)
app.include_router(uploads.router)
app.include_router(jobs.router)
app.include_router(candidates.router)


@app.get("/healthz", tags=["meta"])
async def healthz():
    """Not part of the impl plan §1.4 product endpoint list -- infra liveness probe only
    (impl plan §15.1 D0 checklist: 'API health check passes')."""
    return {"status": "ok"}
