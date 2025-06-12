import asyncio
import json
import sqlite3
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Import from our project structure
from ..schemas.chat_schemas import ChatRequest
from ..core.graph import app
from ..core.agents import AgentState

# --- Database Setup ---
DB_PATH = "chat_history.db"

def init_db():
    """Initializes the SQLite database and creates the history table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

# Initialize the database when the application starts
init_db()

def save_message_to_db(session_id: str, role: str, content: str):
    """Saves a single message to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    conn.commit()
    conn.close()

def get_history_from_db(session_id: str) -> list[BaseMessage]:
    """Retrieves chat history for a session from the database as LangChain objects."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    history = []
    for role, content in cursor.fetchall():
        if role == "user":
            history.append(HumanMessage(content=content))
        elif role == "assistant":
            history.append(AIMessage(content=content))
    conn.close()
    return history

# Create an API router
router = APIRouter()

@router.get("/history/{session_id}")
async def get_history_endpoint(session_id: str):
    """
    New endpoint to fetch chat history for a specific session ID.
    This will be called by the frontend when switching books.
    """
    history = get_history_from_db(session_id)
    # Convert LangChain messages to a JSON-serializable list of dicts
    history_dicts = [{"role": "user" if isinstance(msg, HumanMessage) else "assistant", "content": msg.content} for msg in history]
    return JSONResponse(content={"history": history_dicts})


async def chat_stream_generator(request: ChatRequest):
    """
    This is an async generator that streams the response from our LangGraph agent.
    """
    session_id = request.session_id or f"default_session_{request.book_id}"
    
    chat_history = get_history_from_db(session_id)
    save_message_to_db(session_id, "user", request.question)

    initial_state = AgentState(
        question=request.question,
        book_id=request.book_id,
        messages=chat_history + [HumanMessage(content=request.question)]
    )
    
    final_answer_content = ""
    async for event in app.astream(initial_state, {'recursion_limit': 15}):
        if "generate_final_answer" in event:
            ai_message = event["generate_final_answer"]["messages"][0]
            final_answer_content = ai_message.content
            yield f"data: {json.dumps({'token': final_answer_content})}\n\n"
            await asyncio.sleep(0.01)

    save_message_to_db(session_id, "assistant", final_answer_content)
    print(f"Saved conversation for session '{session_id}' to the database.")

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    The main chat endpoint. It receives a chat request and returns a
    streaming response from the agent.
    """
    return StreamingResponse(
        chat_stream_generator(request), 
        media_type="text/event-stream"
    )
