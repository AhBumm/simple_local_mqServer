"""Producer utilities for enqueuing tasks.

Behavior:
- Require a "prompt" input.
- Normalize the prompt into an internal "graph" representation (key: "graph").
- Persist the queued item as a JSON-line into tasks/queue.jsonl (append-only).

Normalization strategy:
- If prompt is a dict (or JSON object), use it directly as the graph.
- If prompt is a string that contains a JSON object, try to parse it and use the parsed object.
- Otherwise, wrap the prompt string into a simple graph: {"text": <prompt>}.

This keeps the external API simple (clients always send "prompt") while maintaining
an internal "graph" concept for downstream consumers.
"""
import json
import os
import time
import uuid
from typing import Any, Dict

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "queue.jsonl")


def _normalize_prompt_to_graph(prompt: Any) -> Dict:
    """Normalize different prompt shapes into an internal graph representation.

    Returns a dict with key "graph" whose value is either a dict (parsed/used as-is)
    or a wrapper dict containing the original text.
    """
    # If already a mapping/dict-like, assume it's already a graph
    if isinstance(prompt, dict):
        graph = prompt
        return {"graph": graph}

    # If it's a string, try to parse JSON first
    if isinstance(prompt, str):
        stripped = prompt.strip()
        if not stripped:
            raise ValueError("prompt must not be empty")
        # Try to parse as JSON object
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                return {"graph": parsed}
            # If parsed into something else (list/primitive), wrap it
            return {"graph": {"value": parsed}}
        except Exception:
            # Not JSON — treat as plain text prompt
            return {"graph": {"text": prompt}}

    # For any other types, wrap them safely
    return {"graph": {"value": prompt}}


def _append_to_queue(item: Dict) -> None:
    """Append a JSON line to the on-disk queue file.

    The queue file is append-only. This is intentionally simple so the server
    remains lightweight and easy to inspect. Consumers can tail or read the file
    to pick up new tasks.
    """
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False) + "\n")


def enqueue(prompt: Any) -> str:
    """Create a queued task from prompt and persist it.

    Returns the generated task id.
    """
    if prompt is None:
        raise ValueError("prompt is required")

    normalized = _normalize_prompt_to_graph(prompt)

    task_id = uuid.uuid4().hex
    now = int(time.time())

    item = {
        "id": task_id,
        "created_at": now,
        **normalized,
        "status": "queued",
    }

    _append_to_queue(item)

    return task_id
