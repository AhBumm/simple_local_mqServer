# Simple Local MQ Server

This project provides a small local message queue server using Huey. IMPORTANT: the project
now uses FileHuey (file-backed) as the default queue backend. This means Redis is no longer
required by default.

Default behavior
- QUEUE_BACKEND defaults to 'file'.
- File-backed Huey stores its data at FILE_HUEY_PATH (default: ./huey_storage).
- Result persistence uses SQLite (SQLITE_PATH) by default.

Switching to Redis (optional)
If you prefer to use Redis as the backend, do the following:

1. Install the redis client (uncomment or add it to requirements, e.g. `redis==4.7.0`):
   pip install redis

2. Set environment variable:
   export QUEUE_BACKEND=redis
   export REDIS_URL=redis://localhost:6379/0

3. Modify tasks/huey_app.py to initialize a RedisHuey instance instead of FileHuey, for example:

   from huey import RedisHuey
   from config import REDIS_URL, HUEY_NAME

   huey = RedisHuey(name=HUEY_NAME, url=REDIS_URL)

4. Restart the application.

Notes
- FileHuey is convenient for local development and environments where running Redis is not
  desirable. For production environments with higher throughput needs, consider using Redis.
