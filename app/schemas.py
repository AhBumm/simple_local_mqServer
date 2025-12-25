from pydantic import BaseModel
from typing import Any, Dict, Optional

class JobRequest(BaseModel):
    # Minimal fields; ComfyUI should send the graph description and metadata
    graph: Dict[str, Any]
    name: Optional[str] = None
    priority: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = {}

class EnqueueResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Any]
    created_at: str
    updated_at: str
