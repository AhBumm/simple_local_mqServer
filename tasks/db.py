"""
SQLite-backed queue backend for simple_local_mqServer.

Provides a lightweight queue stored in a local SQLite database with basic
enqueue/dequeue/ack semantics and a visibility timeout for processing.
"""
import json
import os
import sqlite3
import time
from typing import Optional, Tuple, Any

DEFAULT_DB_PATH = os.environ.get("SIMPLE_MQ_DB", "queue.sqlite3")


class SQLiteQueue:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._ensure_tables()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    available_at INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    locked_until INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_queue_topic_status_available ON queue(topic, status, available_at);
                """
            )
        finally:
            conn.close()

    def enqueue(self, topic: str, payload: Any, delay_seconds: int = 0) -> int:
        """Enqueue a message. Payload may be a dict or string; it's JSON-serialized.

        Returns the new message id.
        """
        if not isinstance(payload, str):
            payload = json.dumps(payload, ensure_ascii=False)
        now = int(time.time())
        available_at = now + max(0, int(delay_seconds))
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO queue (topic, payload, created_at, available_at, status, locked_until) VALUES (?, ?, ?, ?, 'queued', 0)",
                (topic, payload, now, available_at),
            )
            return cur.lastrowid
        finally:
            conn.close()

    def dequeue(self, topic: str = "default", visibility_timeout: int = 60) -> Optional[Tuple[int, str]]:
        """Attempt to dequeue a single message from the given topic.

        This marks the message as 'processing' and sets locked_until to now + visibility_timeout.
        Returns (id, payload) or None if no available message.
        """
        now = int(time.time())
        lock_until = now + int(visibility_timeout)
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            # Begin immediate transaction to avoid races
            cur.execute("BEGIN IMMEDIATE;")
            cur.execute(
                "SELECT id FROM queue WHERE topic=? AND status='queued' AND available_at<=? ORDER BY id LIMIT 1",
                (topic, now),
            )
            row = cur.fetchone()
            if row is None:
                conn.execute("COMMIT;")
                return None
            msg_id = row[0]
            updated = cur.execute(
                "UPDATE queue SET status='processing', locked_until=? WHERE id=? AND status='queued'",
                (lock_until, msg_id),
            )
            # If update failed due to race, rollback and return None
            if cur.rowcount == 0:
                conn.execute("ROLLBACK;")
                return None
            cur.execute("SELECT id, payload FROM queue WHERE id=?", (msg_id,))
            msg = cur.fetchone()
            conn.execute("COMMIT;")
            if msg is None:
                return None
            return msg[0], msg[1]
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            raise
        finally:
            conn.close()

    def ack(self, message_id: int) -> bool:
        """Acknowledge (remove) a message by id. Returns True if removed."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM queue WHERE id=?", (message_id,))
            return cur.rowcount > 0
        finally:
            conn.close()

    def requeue(self, message_id: int, delay_seconds: int = 0) -> bool:
        """Put a processing message back to queued state (optionally with a delay)."""
        available_at = int(time.time()) + max(0, int(delay_seconds))
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE queue SET status='queued', available_at=?, locked_until=0 WHERE id=?",
                (available_at, message_id),
            )
            return cur.rowcount > 0
        finally:
            conn.close()

    def purge(self) -> int:
        """Delete all messages. Returns number deleted."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM queue")
            return cur.rowcount
        finally:
            conn.close()

    def peek(self, limit: int = 10):
        """Return up to `limit` queued messages (ids and payloads) without changing state."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, topic, payload, created_at, available_at, status FROM queue ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()


# Convenience module-level instance
_default_queue: Optional[SQLiteQueue] = None


def get_default_queue() -> SQLiteQueue:
    global _default_queue
    if _default_queue is None:
        _default_queue = SQLiteQueue()
    return _default_queue


if __name__ == "__main__":
    print("SQLiteQueue DB:", DEFAULT_DB_PATH)
    q = get_default_queue()
    print("Current items:", q.peek(20))
