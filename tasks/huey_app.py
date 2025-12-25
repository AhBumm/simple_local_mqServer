from huey import RedisHuey, SqliteHuey
from typing import Any
import json
from config import QUEUE_BACKEND, REDIS_HOST, REDIS_PORT, REDIS_DB, SQLITE_PATH, HUEY_NAME
from db.result_store import ResultStore

# Create a ResultStore instance so tasks can update status/results.
# NOTE: result_store operations are synchronous; in larger setups use async DB or separate service.
result_store = ResultStore(SQLITE_PATH)

if QUEUE_BACKEND == "redis":
    huey = RedisHuey(name=HUEY_NAME, host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
else:
    huey = SqliteHuey(filename=SQLITE_PATH, name=HUEY_NAME)


@huey.task(retries=3)
def run_comfy_job(job_id: str, payload: Any):
    """
    Generic task entry point that the worker will execute.
    The server enqueues this task with job_id and payload.
    Consumer (worker) must import this same function and implement processing logic here,
    or the worker must check DB for job payload and perform computation.

    Currently this placeholder marks status; actual image generation / graph execution
    should be implemented in the consumer process.
    """
    # Mark processing start
    result_store.update_status(job_id, "processing")
    # The real execution belongs to the consumer. For now we record a placeholder.
    try:
        # If the consumer implements execution here (when running worker),
        # replace the following block with actual ComfyUI graph execution code.
        # For the server-only design, we don't execute.
        # Simulate work or leave as no-op.
        # Example of where consumer would:
        # result = execute_comfy_graph(payload)
        result = {"status": "noop", "note": "no consumer implemented yet"}
        result_store.save_result(job_id, result)
        result_store.update_status(job_id, "finished")
        return result
    except Exception as exc:
        result_store.save_result(job_id, {"error": str(exc)})
        result_store.update_status(job_id, "failed")
        raise
