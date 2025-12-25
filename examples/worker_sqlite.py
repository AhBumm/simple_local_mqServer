"""
Example worker that consumes messages from the SQLite-backed queue.

This demonstrates simple consumption with acknowledgement and a visibility timeout.
"""
import signal
import sys
import time
import logging

from tasks.db import SQLiteQueue, get_default_queue

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

stop = False


def handle_signal(signum, frame):
    global stop
    logger.info("Received signal, stopping...")
    stop = True


def process_message(payload):
    # Replace with real work
    logger.info("Processing payload: %r", payload)
    # simulate work
    time.sleep(1)


def main(db_path: str = None, topic: str = "default"):
    if db_path:
        q = SQLiteQueue(db_path)
    else:
        q = get_default_queue()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logger.info("Worker started, topic=%s db=%s", topic, db_path or "default")
    while not stop:
        msg = q.dequeue(topic=topic, visibility_timeout=30)
        if not msg:
            time.sleep(1)
            continue
        msg_id, payload_text = msg
        # try to parse JSON payload
        try:
            import json

            payload = json.loads(payload_text)
        except Exception:
            payload = payload_text

        try:
            process_message(payload)
            q.ack(msg_id)
            logger.info("Message %s acked", msg_id)
        except Exception:
            logger.exception("Error processing message %s, requeueing", msg_id)
            q.requeue(msg_id, delay_seconds=5)

    logger.info("Worker exiting")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", help="Path to sqlite DB (default uses env SIMPLE_MQ_DB or queue.sqlite3)")
    parser.add_argument("--topic", default="default")
    args = parser.parse_args()
    main(db_path=args.db, topic=args.topic)
