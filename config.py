from typing import Optional
import os

# Basic configuration via env
QUEUE_BACKEND = os.getenv("QUEUE_BACKEND", "redis")  # "redis" or "sqlite"
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
SQLITE_PATH = os.getenv("SQLITE_PATH", "comfy_queue.db")
AUTH_TOKEN = os.getenv("COMFY_QUEUE_TOKEN", None)  # simple bearer token for HTTP API
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
HUEY_NAME = os.getenv("HUEY_NAME", "comfyui")
