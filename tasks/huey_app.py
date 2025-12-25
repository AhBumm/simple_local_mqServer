"""
Huey app instance using SqliteHuey as default backend.

This module exposes:
- huey: SqliteHuey instance used by producer/consumer
- result_store: our local SQLite-backed ResultStore for job metadata/results
"""

import os
from huey import SqliteHuey
from typing import Any
from config import HUEY_SQLITE_PATH, HUEY_NAME, SQLITE_PATH, QUEUE_BACKEND
from db.result_store import ResultStore

# Ensure parent directory exists for SQLite file
parent = os.path.dirname(HUEY_SQLITE_PATH) or '.'
os.makedirs(parent, exist_ok=True)

# Instantiate Huey. We use SqliteHuey by default (file-backed SQLite).
# If you later want Redis, change to RedisHuey(...) and adjust requirements.
huey = SqliteHuey(filename=HUEY_SQLITE_PATH, name=HUEY_NAME)

# Our separate ResultStore for job metadata / result indexing (keeps same schema)
result_store = ResultStore(SQLITE_PATH)


@huey.task(retries=3)
def run_comfy_job(job_id: str, payload: Any):
    """
    Placeholder task: consumer running this will (in a real system) execute the ComfyUI graph.
    Keep it minimal here; consumer can either execute directly here or call out to worker logic.
    """
    # Check DB cancellation/guard before executing
    job = result_store.get_job(job_id)
    if job and job.get("status") == "cancelled":
        result_store.save_result(job_id, {"status": "cancelled", "note": "job cancelled before execution"})
        return {"status": "cancelled"}

    # Mark processing start
    result_store.update_status(job_id, "processing")
    try:
        # Placeholder: actual ComfyUI graph execution should be implemented by the consumer.
        result = {"status": "noop", "note": "no consumer implemented yet"}
        result_store.save_result(job_id, result)
        result_store.update_status(job_id, "finished")
        return result
    except Exception as exc:
        result_store.save_result(job_id, {"error": str(exc)})
        result_store.update_status(job_id, "failed")
        raise
