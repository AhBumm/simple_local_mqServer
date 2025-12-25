import os

# Queue backend selection: default to sqlite-backed Huey (SqliteHuey)
QUEUE_BACKEND = os.getenv('QUEUE_BACKEND', 'sqlite')  # 'sqlite' | 'file' | 'redis'

# SqliteHuey DB file (used for Huey queue storage)
HUEY_SQLITE_PATH = os.getenv('HUEY_SQLITE_PATH', './huey_queue.sqlite')

# Separate SQLite path used by our ResultStore for job metadata/results (can be same or different)
SQLITE_PATH = os.getenv('SQLITE_PATH', './huey_results.sqlite')

# Huey name
HUEY_NAME = os.getenv('HUEY_NAME', 'simple_local_mq')

# Redis settings (kept for optional use)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

# API / auth
AUTH_TOKEN = os.getenv('COMFY_QUEUE_TOKEN', None)
API_HOST = os.getenv('API_HOST', '127.0.0.1')
API_PORT = int(os.getenv('API_PORT', '8000'))
