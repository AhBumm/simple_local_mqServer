"""
Producer using the SQLite-backed queue (tasks/db.SQLiteQueue).

Replace or adapt existing producer usage to call SQLiteQueue.enqueue
so the system uses the SQLite-backed queue instead of file/JSONL-based queues.
"""
import argparse
import json
import os
from typing import Any

from .db import SQLiteQueue, get_default_queue


def send_message(topic: str, payload: Any, db_path: str = None, delay: int = 0) -> int:
    if db_path:
        q = SQLiteQueue(db_path)
    else:
        q = get_default_queue()
    return q.enqueue(topic, payload, delay_seconds=delay)


def main():
    parser = argparse.ArgumentParser(description="Send a message to the SQLite-backed queue")
    parser.add_argument("topic", nargs="?", default="default")
    parser.add_argument("message", nargs="?", help="Message payload (JSON or plain text). If omitted, reads from stdin.")
    parser.add_argument("--db", help="Path to sqlite DB (default: env SIMPLE_MQ_DB or queue.sqlite3)")
    parser.add_argument("--delay", type=int, default=0, help="Delay in seconds before the message becomes available")
    args = parser.parse_args()

    if args.message is None:
        import sys

        payload = sys.stdin.read().strip()
    else:
        payload = args.message

    # Try to parse as JSON; if fails keep as string
    try:
        parsed = json.loads(payload)
    except Exception:
        parsed = payload

    msg_id = send_message(args.topic, parsed, db_path=args.db, delay=args.delay)
    print(f"Enqueued message id={msg_id} topic={args.topic}")


if __name__ == "__main__":
    main()
