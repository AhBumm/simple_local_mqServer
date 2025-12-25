Simplified API (prompt-only) for simple_local_mqServer

Overview

This repository provides a tiny local message queueing server. The API has been simplified so that task submissions are centered around a single required field: "prompt" — a string containing the full workflow encoded as a JSON string.

POST /tasks

Request JSON body fields:
- prompt (string, required): A JSON-encoded string representing the full workflow/payload. The server validates that this is valid JSON (i.e. json.loads(prompt) must succeed).
- priority (integer, optional): Task priority. Defaults to 1 if omitted.
- metadata (object, optional): May only include the keys 'prompt_id' and 'create_time'. If either is missing, the server will generate them.

Examples

Request

{
  "prompt": "{\"op\": \"echo\", \"value\": \"hello\"}",
  "priority": 5
}

Response

{
  "status": "queued",
  "task": {
    "prompt": "{\"op\": \"echo\", \"value\": \"hello\"}",
    "priority": 5,
    "metadata": {
      "prompt_id": "generated-or-provided-id",
      "create_time": "2025-12-25T08:53:49Z"
    }
  }
}

Storage

Submitted tasks are appended as newline-delimited JSON (JSON Lines / .jsonl) to:

  tasks/queue.jsonl

Each line contains one JSON object representing the queued task.

Notes

- The server strictly validates that the 'prompt' field is a JSON string. If it's not valid JSON, the request will be rejected with HTTP 400.
- The metadata field is intentionally minimal to keep the interface simple and predictable.

Running the server

Install requirements (e.g. fastapi + uvicorn) and run:

  uvicorn app.main:app --reload --port 8000

Contributing

If you need a richer metadata surface or different persistence, consider extending tasks/producer.py and the API validation in app/main.py accordingly.
