from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    """
    Defines the structure for an incoming chat request.
    """
    question: str
    book_id: str # The unique identifier for the book being discussed (e.g., "fluent_python")
    session_id: Optional[str] = None # Optional session ID for tracking conversation history

class ChatResponse(BaseModel):
    """
    Defines the structure for a chat response.
    This is not used for streaming, but good practice for potential non-streaming endpoints.
    """
    answer: str
    sources: List[Dict[str, Any]] = []

