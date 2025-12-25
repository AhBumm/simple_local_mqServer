from fastapi import FastAPI
import os
from config import QUEUE_BACKEND, FILE_HUEY_PATH

app = FastAPI()


@app.get("/health")
async def health():
    """Simple health endpoint.

    For file-backed Huey (default), checks that the FILE_HUEY_PATH exists or is listable.
    For other backends (e.g. Redis), this endpoint gives a basic response; you can extend
    it to perform backend-specific health checks if needed.
    """
    backend = QUEUE_BACKEND or 'file'
    details = {"queue_backend": backend}
    healthy = True

    if backend in ('file', 'sqlite'):
        path = FILE_HUEY_PATH
        details['file_huey_path'] = path
        try:
            # If it's a directory, try listing; if it's a file path, try listing its parent
            if os.path.isdir(path):
                os.listdir(path)
            else:
                parent = os.path.dirname(path) or '.'
                os.listdir(parent)
        except Exception as e:
            healthy = False
            details['error'] = f'File backend check failed: {e}'
    else:
        # For Redis or other backends we intentionally avoid inspecting backend-specific
        # internal objects here (previous code relied on huey.store which is Redis-specific).
        # If you use Redis, consider implementing a ping to the Redis server here.
        details['note'] = 'No detailed health check implemented for non-file backends.'

    return {"ok": healthy, "details": details}
