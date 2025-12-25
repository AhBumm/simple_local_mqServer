"""Huey app instance

This module exposes a Huey instance used by the application. The project now uses FileHuey
as the default backend (file-backed storage) so Redis is no longer required by default.

If you need to use Redis instead, set QUEUE_BACKEND='redis' and modify this module to
initialize a RedisHuey instance (and install the redis client).

Health checks in the app assume file-backed storage by default.
"""

import os
from huey import FileHuey, ResultStore
from config import FILE_HUEY_PATH, HUEY_NAME, SQLITE_PATH

# Ensure storage directory exists for FileHuey (if a directory path is used)
# FileHuey may accept a filename or directory depending on version; ensure parent dir exists.
try:
    # If FILE_HUEY_PATH is a directory, create it. If it's a file path, make sure parent exists.
    if os.path.isdir(FILE_HUEY_PATH) or FILE_HUEY_PATH.endswith(os.sep):
        os.makedirs(FILE_HUEY_PATH, exist_ok=True)
    else:
        parent = os.path.dirname(FILE_HUEY_PATH) or '.'
        os.makedirs(parent, exist_ok=True)
except Exception:
    # Not fatal here; Huey/FileHuey will raise errors if it cannot write to the path.
    pass

# Initialize Huey using file-backed storage by default
# Filename/path/dir argument name depends on Huey version; many versions accept 'filename'
huey = FileHuey(filename=FILE_HUEY_PATH, name=HUEY_NAME)

# Keep a result store (SQLite) for task results; this is independent of the queue backend
# ResultStore may accept a filename for SQLite-based result persistence.
result_store = ResultStore(SQLITE_PATH)

# Export any other helpers or task decorators as needed by the rest of the codebase


__all__ = ['huey', 'result_store']
