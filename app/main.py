from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
import tasks.producer as producer

app = FastAPI(title="simple_local_mqServer")

class EnqueueRequest(BaseModel):
    """Request payload for enqueue endpoint.
    The API enforces a prompt-only payload. "prompt" can be a string,
    a JSON-serializable object, or any value that represents the user's prompt.
    """
    prompt: Any


@app.post("/enqueue")
async def enqueue(req: EnqueueRequest):
    """Enqueue a new task.

    The endpoint requires a JSON object with a single key "prompt".
    The producer normalizes the prompt into an internal "graph" representation
    before persisting it to the local queue.
    """
    prompt = req.prompt
    if prompt is None or (isinstance(prompt, str) and prompt.strip() == ""):
        raise HTTPException(status_code=400, detail="'prompt' must be provided and non-empty")

    try:
        task_id = producer.enqueue(prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue task: {e}")

    return {"id": task_id, "status": "queued"}


@app.get("/")
async def root():
    return {"msg": "simple_local_mqServer running. Use POST /enqueue with { \"prompt\": ... }"}
