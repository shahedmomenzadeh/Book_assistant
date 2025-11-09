import os
import shutil
import subprocess
import sys
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

# Construct robust paths to necessary directories and scripts from the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
DATA_DIR = os.path.join(project_root, 'data')
INGESTION_SCRIPT_PATH = os.path.join(project_root, 'scripts', 'ingest_book.py')
VECTOR_STORE_DIR = os.path.join(project_root, 'vector_store')


router = APIRouter()

@router.post("/upload")
async def upload_book(file: UploadFile = File(...)):
    """
    Handles the upload of a new PDF book.
    It saves the book and triggers a targeted ingestion for ONLY the new book.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")

    file_path = os.path.join(DATA_DIR, file.filename)

    # Save the uploaded file to the 'data' directory
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"File '{file.filename}' saved to '{file_path}'")
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    # Trigger the ingestion script to process ONLY the new book
    print(f"Triggering targeted ingestion for '{file.filename}'...")
    try:
        python_executable = sys.executable
        # Pass the specific filename to the ingestion script using the --file argument
        result = subprocess.run(
            [python_executable, INGESTION_SCRIPT_PATH, "--file", file.filename],
            capture_output=True,
            text=True,
            check=True  # Raise an exception if the script returns a non-zero exit code
        )
        print("Ingestion script stdout:", result.stdout)
        if result.stderr:
            print("Ingestion script stderr:", result.stderr)

    except subprocess.CalledProcessError as e:
        # If the script fails, provide the error output for debugging
        print(f"Ingestion script failed with exit code {e.returncode}")
        print("Error output:", e.stderr)
        raise HTTPException(status_code=500, detail=f"Failed to process the new book. Error: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during ingestion: {e}")

    return JSONResponse(
        status_code=200,
        content={"message": f"Book '{file.filename}' uploaded and processed successfully."}
    )

@router.get("/list")
async def list_books():
    """
    Returns a list of available books by scanning the vector_store directory.
    A directory is considered a valid book if it contains an 'index.faiss' file.
    This allows the frontend to dynamically update the list of available books.
    """
    if not os.path.exists(VECTOR_STORE_DIR):
        return JSONResponse(content={"books": []})
    
    try:
        available_books = []
        for d in os.listdir(VECTOR_STORE_DIR):
            book_path = os.path.join(VECTOR_STORE_DIR, d)
            # A book is only valid if it's a directory AND contains the FAISS index file
            if os.path.isdir(book_path) and os.path.exists(os.path.join(book_path, "index.faiss")):
                available_books.append(d)
        return JSONResponse(content={"books": available_books})
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Could not read book directory: {e}")

