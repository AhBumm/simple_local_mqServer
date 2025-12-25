ComfyUI Huey Queue (simple_local_mqServer)

This project provides a minimal FastAPI-based queue server for submitting ComfyUI graph jobs and storing job metadata/results locally. The server uses Huey as the task queue. By default, the project is configured to use Huey's SqliteHuey (a file-backed SQLite queue) and keeps a separate SQLite database for the ResultStore (job metadata/results).

Highlights
- Default queue backend: SqliteHuey (file-backed Huey) stored at ./huey_queue.sqlite
- Separate ResultStore DB: ./huey_results.sqlite (stores job metadata and results)
- Simple REST API to enqueue jobs, check status, retrieve results and cancel jobs
- Optional: switch to Redis-based Huey by setting QUEUE_BACKEND and installing redis client

Getting started
1. Install dependencies:

   pip install -r requirements.txt

2. Run the API server (development):

   uvicorn app.main:app --reload

3. Enqueue a job (example):

   POST /enqueue
   {
     "graph": {...},
     "name": "example job",
     "priority": 1,
     "metadata": {"user": "alice"}
   }

Notes on SqliteHuey and ResultStore
- SqliteHuey stores Huey job queue data in a SQLite file (HUEY_SQLITE_PATH). This is suitable for local/small setups and testing.
- This project intentionally keeps a separate SQLite DB (SQLITE_PATH) for the ResultStore to manage job metadata and results. Keeping them separate helps avoid contention and allows different retention/backup strategies.
- If you want to use Redis for the queue backend instead, set QUEUE_BACKEND=redis and install a Redis client (see requirements comment). You will also need to modify tasks/huey_app.py to instantiate RedisHuey.

Environment variables (overrides)
- QUEUE_BACKEND: 'sqlite' | 'file' | 'redis' (default: sqlite)
- HUEY_SQLITE_PATH: path to Huey SQLite DB (default: ./huey_queue.sqlite)
- SQLITE_PATH: path to ResultStore SQLite DB (default: ./huey_results.sqlite)
- HUEY_NAME: name for Huey instance (default: simple_local_mq)
- COMFY_QUEUE_TOKEN: optional Bearer token for API auth
- API_HOST / API_PORT: host/port for the FastAPI server

License
- (Add your license information here)
