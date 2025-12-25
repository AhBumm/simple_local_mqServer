import sqlite3
import json
import threading
from typing import Optional, Any, Dict
import datetime

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT,
    payload TEXT,
    result TEXT,
    created_at TEXT,
    updated_at TEXT
);
"""

class ResultStore:
    """
    Very small synchronous SQLite-backed job metadata/result store.
    For local use and testing. For production consider Redis, Postgres, etc.
    """
    def __init__(self, db_path: str = "comfy_queue.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        with self._get_conn() as conn:
            conn.execute(CREATE_SQL)
            conn.commit()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return conn

    def _now(self) -> str:
        return datetime.datetime.utcnow().isoformat() + "Z"

    def create_job(self, job_id: str, payload: Dict):
        now = self._now()
        with self._lock, self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO jobs (job_id, status, payload, result, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, "queued", json.dumps(payload), json.dumps({}), now, now)
            )
            conn.commit()

    def update_status(self, job_id: str, status: str):
        now = self._now()
        with self._lock, self._get_conn() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (status, now, job_id)
            )
            conn.commit()

    def save_result(self, job_id: str, result: Any):
        now = self._now()
        with self._lock, self._get_conn() as conn:
            conn.execute(
                "UPDATE jobs SET result = ?, updated_at = ? WHERE job_id = ?",
                (json.dumps(result), now, job_id)
            )
            conn.commit()

    def get_job(self, job_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            cur = conn.execute("SELECT job_id, status, payload, result, created_at, updated_at FROM jobs WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "job_id": row[0],
                "status": row[1],
                "payload": json.loads(row[2]) if row[2] else None,
                "result": json.loads(row[3]) if row[3] else None,
                "created_at": row[4],
                "updated_at": row[5],
            }

    def list_jobs(self, limit: int = 100):
        with self._get_conn() as conn:
            cur = conn.execute("SELECT job_id, status, created_at, updated_at FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return [
                {"job_id": r[0], "status": r[1], "created_at": r[2], "updated_at": r[3]}
                for r in rows
            ]

    def cancel_job(self, job_id: str) -> bool:
        """
        Mark job as cancelled if it's still queued. Actual removal from Huey queue
        is worker-backend-specific; Huey supports reverting or code-level revokes but
        for simplicity we mark as 'cancelled' and consumer should check status before processing.
        """
        job = self.get_job(job_id)
        if not job:
            return False
        if job["status"] in ("queued", "retry"):
            self.update_status(job_id, "cancelled")
            return True
        return False
