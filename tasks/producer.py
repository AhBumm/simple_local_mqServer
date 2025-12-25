from uuid import uuid4
from tasks.huey_app import run_comfy_job, result_store
from typing import Dict, Any

def enqueue_comfy_job(payload: Dict[str, Any]) -> str:
    """
    Create a job_id, persist metadata, and enqueue the Huey task.
    The payload can contain the ComfyUI graph description, node inputs, etc.
    Returns job_id.
    """
    job_id = str(uuid4())
    # Save metadata in local store
    result_store.create_job(job_id, payload)
    # Enqueue the Huey task (worker will pick this up)
    # We pass the job_id and payload; worker can re-load payload from DB if desired.
    run_comfy_job.enqueue(job_id, payload)
    return job_id
