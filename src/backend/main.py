from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the routers from our api module
from .api import chat, books # Added books router

# Create the main FastAPI application instance
app = FastAPI(
    title="Multi-Agent Programming Tutor API",
    description="An API for a multi-agent system to help study programming books.",
    version="1.0.0"
)

# --- CORS (Cross-Origin Resource Sharing) ---
# This is crucial for allowing our Streamlit frontend (running on a different port)
# to communicate with this FastAPI backend.
origins = [
    "http://localhost",
    "http://localhost:8501",  # Default port for Streamlit
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers 
)

# --- Include Routers ---
# We add tags to group related endpoints in the automatic API docs (e.g., at /docs)
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(books.router, prefix="/api/v1/books", tags=["Books"]) # Added books router

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the Multi-Agent Programming Tutor API!"}