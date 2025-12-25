# simple_local_mqServer

This repository contains a reference implementation for a local ComfyUI task queue server based on Huey.

It provides a FastAPI HTTP API to enqueue jobs, check status, retrieve results, list jobs, cancel jobs, and perform basic health checks. The queue backend can be Redis (recommended) or SQLite for single-machine testing.

Quickstart

1. Create and activate a virtualenv:
   - python -m venv venv
   - source venv/bin/activate
2. Install dependencies:
   - pip install -r requirements.txt
3. Configure environment variables (optional):
   - QUEUE_BACKEND=redis
   - REDIS_HOST=127.0.0.1
   - REDIS_PORT=6379
   - COMFY_QUEUE_TOKEN=yourtoken
4. Run the API server:
   - uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

API endpoints

- POST /enqueue - Enqueue a job
- GET /status/{job_id} - Check job status and metadata
- GET /result/{job_id} - Retrieve job result
- GET /jobs - List recent jobs
- POST /cancel/{job_id} - Cancel a queued job
- GET /health - Health check
- GET /metrics - Basic metrics (placeholder)

Notes

- This repository contains server-side code only. Worker/consumer implementation is intentionally omitted and will be implemented separately.
- For production use prefer RedisHuey + an external result store (Postgres/Redis/S3 for big artifacts).
