import os

# Queue backend selection: default to file-backed Huey (FileHuey)
# Possible values: 'file', 'redis', 'sqlite' (the app uses file by default)
QUEUE_BACKEND = os.getenv('QUEUE_BACKEND', 'file')  # default is 'file' (FileHuey)

# FileHuey storage path (used when QUEUE_BACKEND is 'file')
# This will be a directory (or a file path depending on implementation). Default is './huey_storage'
FILE_HUEY_PATH = os.getenv('FILE_HUEY_PATH', './huey_storage')

# Huey name
HUEY_NAME = os.getenv('HUEY_NAME', 'simple_local_mq')

# SQLite path used for result store / local storage of results
SQLITE_PATH = os.getenv('SQLITE_PATH', './huey_results.sqlite')

# Redis settings (kept for optional Redis usage; not required by default)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

# Comments:
# - The default QUEUE_BACKEND is 'file' (FileHuey). To switch to Redis, set QUEUE_BACKEND='redis'
#   and ensure you install the redis client (uncomment/add it to requirements or install separately).
# - FILE_HUEY_PATH controls where FileHuey stores its files. Ensure this path is writable by the app.
