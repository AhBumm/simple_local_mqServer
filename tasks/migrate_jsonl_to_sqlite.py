"""
Migration script: import messages from a JSONL file into the SQLite queue.

Each line in the input file is expected to be a JSON object. Supported formats:
- {"topic": "mytopic", "payload": {...}}  <-- recommended
- {"topic": "mytopic", "message": ...}
- any JSON value (treated as payload with topic default)

If a line is plain text (not JSON), it will be enqueued as payload (topic default).
"""
import argparse
import json
import os
import sys
from typing import Any

from .db import SQLiteQueue, get_default_queue


def migrate(jsonl_path: str, sqlite_path: str = None, topic: str = "default") -> int:
    if sqlite_path:
        q = SQLiteQueue(sqlite_path)
    else:
        q = get_default_queue()

    count = 0
    with open(jsonl_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            payload = None
            t = topic
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    if "topic" in obj and "payload" in obj:
                        t = obj.get("topic", t)
                        payload = obj.get("payload")
                    elif "topic" in obj and "message" in obj:
                        t = obj.get("topic", t)
                        payload = obj.get("message")
                    elif "topic" in obj and len(obj) == 1:
                        # only topic provided -> skip
                        continue
                    else:
                        # treat whole object as payload
                        payload = obj
                else:
                    # JSON value (string/number/etc) use as payload
                    payload = obj
            except json.JSONDecodeError:
                # plain text line
                payload = line

            q.enqueue(t, payload)
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Migrate a JSONL queue file into SQLite-backed queue")
    parser.add_argument("jsonl", help="Path to input JSONL file")
    parser.add_argument("--sqlite", help="Path to sqlite DB to write (if omitted uses default)")
    parser.add_argument("--topic", default="default", help="Default topic for messages that don't specify one")
    args = parser.parse_args()

    if not os.path.exists(args.jsonl):
        print("Input file not found:", args.jsonl, file=sys.stderr)
        sys.exit(2)

    count = migrate(args.jsonl, sqlite_path=args.sqlite, topic=args.topic)
    print(f"Migrated {count} messages from {args.jsonl} to SQLite DB {args.sqlite or 'default'}")


if __name__ == "__main__":
    main()
