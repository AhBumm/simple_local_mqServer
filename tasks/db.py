# default cached instance and helper
_default_queue = None

def get_default_queue() -> SQLiteQueue:
    """
    Return a cached SQLiteQueue instance using the SIMPLE_MQ_DB env var or
    fallback to 'queue.sqlite3' in the repo root. This avoids recreating
    connections repeatedly and provides a convenient default.
    """
    global _default_queue
    if _default_queue is None:
        db_path = os.environ.get("SIMPLE_MQ_DB", "queue.sqlite3")
        _default_queue = SQLiteQueue(db_path)
    return _default_queue
