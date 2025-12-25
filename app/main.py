from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import uuid
import datetime

from tasks.producer import enqueue_task

app = FastAPI(title="simple_local_mqServer")

class TaskRequest(BaseModel):
    prompt: str
    priority: Optional[int] = 1
    metadata: Optional[Dict[str, Any]] = None


@app.post('/tasks')
async def create_task(req: TaskRequest):
    # Validate that prompt is a JSON string (i.e. string containing valid JSON)
    try:
        _ = json.loads(req.prompt)
    except Exception:
        raise HTTPException(status_code=400, detail="'prompt' must be a valid JSON string")

    metadata = req.metadata or {}
    allowed_keys = {'prompt_id', 'create_time'}

    # Reject any extraneous metadata keys
    extra_keys = set(metadata.keys()) - allowed_keys
    if extra_keys:
        raise HTTPException(
            status_code=400,
            detail=f"metadata may only contain the keys: {sorted(list(allowed_keys))}. unexpected: {sorted(list(extra_keys))}"
        )

    # Generate prompt_id and create_time if missing
    if 'prompt_id' not in metadata or not metadata.get('prompt_id'):
        metadata['prompt_id'] = uuid.uuid4().hex
    if 'create_time' not in metadata or not metadata.get('create_time'):
        metadata['create_time'] = datetime.datetime.utcnow().isoformat() + 'Z'

    task = {
        'prompt': req.prompt,
        'priority': req.priority,
        'metadata': metadata,
    }

    try:
        enqueue_task(task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to enqueue task: {e}")

    return {'status': 'queued', 'task': task}


# If you want to run the app directly for development:
# uvicorn app.main:app --reload --port 8000
