from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional, List
from tasks.producer import enqueue_comfy_job
from db.result_store import ResultStore
from app import schemas
from config import AUTH_TOKEN, SQLITE_PATH, API_HOST, API_PORT
from tasks.huey_app import result_store, huey
import uvicorn
import os

app = FastAPI(title="ComfyUI Huey Queue (server)")

# Simple auth dependency
def check_token(authorization: Optional[str]):
    if AUTH_TOKEN is None:
        return True
    if not authorization:
        return False
    if not authorization.startswith("Bearer "):
        return False
    token = authorization.split(" ", 1)[1]
    return token == AUTH_TOKEN

@app.middleware("http")
async def simple_auth_middleware(request: Request, call_next):
    # Allow health and metrics unauthenticated
    if request.url.path in ("/health", "/metrics"):
        return await call_next(request)
    auth = request.headers.get("Authorization")
    if not check_token(auth):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return await call_next(request)

@app.post("/enqueue", response_model=schemas.EnqueueResponse)
def api_enqueue(req: schemas.JobRequest):
    """
    Enqueue a ComfyUI job. Payload should contain the graph and any needed data.
    """
    payload = {
        "graph": req.graph,
        "name": req.name,
        "priority": req.priority,
        "metadata": req.metadata
    }
    job_id = enqueue_comfy_job(payload)
    return {"job_id": job_id, "status": "queued"}

@app.get("/status/{job_id}", response_model=schemas.JobStatusResponse)
def api_status(job_id: str):
    job = result_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "result": job.get("result"),
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
            }

@app.get("/result/{job_id}")
def api_result(job_id: str):
    job = result_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job.get("result")

app.get("/jobs")
def api_list(limit: int = 100):
    return result_store.list_jobs(limit=limit)

app.post("/cancel/{job_id}")
def api_cancel(job_id: str):
    ok = result_store.cancel_job(job_id)
    if not ok:
        raise HTTPException(status_code=400, detail="cannot cancel (not found or already running/finished)")
    return {"job_id": job_id, "status": "cancelled"}

app.get("/health")
def api_health():
    # basic health checks
    backends = {"sqlite": os.path.exists(SQLITE_PATH)}
    # Try huey ping if Redis backend:
    try:
        # RedisHuey exposes a 'consumer' infra; but we can attempt to access backend connection
        if hasattr(huey, "store") and getattr(huey, "store") is not None:
            # some huey stores expose client property
            backends["huey"] = True
    except Exception:
        backends["huey"] = False
    return {"ok": True, "backends": backends}

# Optional metrics endpoint (placeholder)
app.get("/metrics")
def metrics():
    # For full prometheus support integrate prometheus_client
    return PlainTextResponse("comfy_queue_jobs_total 0\n")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=True)
