import sqlite3
import json
import uuid
import threading
from typing import Optional, Tuple, Any


class ResultStore:
    """Simple SQLite-backed result store.

    Provides methods to create jobs, atomically claim a queued job (marking it processing),
    save results, and mark jobs failed.
    """

    def __init__(self, db_path: str = "results.db"):
        self.db_path = db_path
        # sqlite connections are not thread-safe by default; we open/close per operation
        self._init_db()
        # lightweight lock used to serialize init (and any non-transactional ops)
        self._lock = threading.Lock()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        # enable WAL for better concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    payload TEXT,
                    status TEXT NOT NULL,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # trigger to update updated_at
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS jobs_updated_at
                AFTER UPDATE ON jobs
                BEGIN
                    UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
                """
            )

    def create_job(self, payload: Any) -> str:
        """Create a new job in queued state and return job_id."""
        job_id = str(uuid.uuid4())
        payload_json = json.dumps(payload)
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO jobs (id, payload, status) VALUES (?, ?, ?)",
                (job_id, payload_json, "queued"),
            )
        return job_id

    def claim_job(self) -> Optional[Tuple[str, Any]]:
        """
        Atomically select one queued job and mark it as processing.

        Returns (job_id, payload) or None if no queued job is available.

        Uses a transaction to ensure the select-and-update is atomic: we select the oldest queued job
        and then attempt to update its status from 'queued' to 'processing'. If the update affected
        0 rows another worker claimed it first and we loop to try again.
        """
        # We'll try to find and claim a job in a loop to handle races.
        conn = self._get_conn()
        try:
            while True:
                try:
                    # Begin immediate transaction to acquire write lock
                    conn.execute("BEGIN IMMEDIATE")
                    row = conn.execute(
                        "SELECT id, payload FROM jobs WHERE status = 'queued' ORDER BY created_at LIMIT 1"
                    ).fetchone()
                    if row is None:
                        conn.execute("COMMIT")
                        return None

                    job_id = row["id"]
                    payload_text = row["payload"]

                    # Attempt to claim this job: only succeed if still queued
                    cur = conn.execute(
                        "UPDATE jobs SET status = 'processing' WHERE id = ? AND status = 'queued'",
                        (job_id,),
                    )
                    if cur.rowcount == 1:
                        conn.execute("COMMIT")
                        payload = json.loads(payload_text) if payload_text is not None else None
                        return job_id, payload

                    # else, someone else claimed it in the meantime; loop to try again
                    conn.execute("ROLLBACK")
                except sqlite3.OperationalError:
                    # If database is busy or some other transient issue, rollback and retry once
                    try:
                        conn.execute("ROLLBACK")
                    except Exception:
                        pass
                    return None
        finally:
            conn.close()

    def save_result(self, job_id: str, result: Any, status: str = "success") -> bool:
        """Save result for a job and update its status (e.g. "success" or "failed").

        Returns True if job updated, False otherwise.
        """
        result_json = json.dumps(result)
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE jobs SET result = ?, status = ? WHERE id = ?",
                (result_json, status, job_id),
            )
            return cur.rowcount == 1

    def set_failed(self, job_id: str, message: Optional[str] = None) -> bool:
        """Mark a job as failed and optionally store failure message."""
        payload = {"error": message} if message is not None else None
        payload_json = json.dumps(payload) if payload is not None else None
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE jobs SET status = 'failed', result = ? WHERE id = ?",
                (payload_json, job_id),
            )
            return cur.rowcount == 1

    def get(self, job_id: str) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "payload": json.loads(row["payload"]) if row["payload"] else None,
                "status": row["status"],
                "result": json.loads(row["result"]) if row["result"] else None,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
