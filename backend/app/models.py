from pydantic import BaseModel
from typing import Optional, List, Dict

class ChatRequest(BaseModel):
    session_id: str
    text: str

class ChatResponse(BaseModel):
    reply: str
    language: str
    intent: str
    state: str
    collected_fields: Dict[str, Optional[str]]
    citations: List[Dict[str, str]] = []
    ticket_id: Optional[str] = None
    escalated: bool = False