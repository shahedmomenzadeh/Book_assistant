import os
import shutil
import sys
import argparse
from dotenv import load_dotenv
from typing import List
from langchain.docstore.document import Document

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
except ImportError:
    print("One or more required libraries are not installed.")
    print("Please run: pip install pypdf langchain-google-genai langchain faiss-cpu")
    sys.exit(1)

# --- CONFIGURATION ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), '..', 'vector_store')

# --- CORE LOGIC ---
def create_vector_db_for_book(file_path: str, book_id: str):
    """Creates and saves a FAISS vector store for a single book."""
    print(f"\n--- Processing book: {book_id} ---")
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    try:
        loader = PyPDFLoader(file_path=file_path)
        documents = loader.load()
        print(f"-> Loaded {len(documents)} pages.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(documents)
        print(f"-> Split into {len(docs)} chunks.")

        for doc in docs:
            doc.page_content = doc.page_content.encode('utf-8', 'ignore').decode('utf-8')

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        print("-> Creating FAISS index...")
        db = FAISS.from_documents(docs, embeddings)

        # --- ATOMIC SAVE ---
        # 1. Save to a temporary directory
        temp_dir = os.path.join(VECTOR_STORE_DIR, f"temp_{book_id}_{os.getpid()}")
        db.save_local(temp_dir)

        # 2. Rename the directory to the final name
        final_dir = os.path.join(VECTOR_STORE_DIR, book_id)
        if os.path.exists(final_dir):
            shutil.rmtree(final_dir) # Remove old version if it exists
        os.rename(temp_dir, final_dir)

        print(f"-> FAISS index saved to: {final_dir}")

    except Exception as e:
        print(f"!!-> Failed to process {book_id}. Error: {e}")
        # Clean up temporary directory if it exists
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def run_ingestion_pipeline(target_file: str = None):
    """
    Main ingestion pipeline.
    If a target_file is provided, it processes only that file.
    Otherwise, it processes all PDF files in the data directory.
    """
    if not os.path.exists(VECTOR_STORE_DIR):
        os.makedirs(VECTOR_STORE_DIR)
        print(f"Created directory: {VECTOR_STORE_DIR}")

    if target_file:
        pdf_files = [target_file] if target_file.endswith('.pdf') else []
        if not os.path.exists(os.path.join(DATA_DIR, target_file)):
             print(f"Specified file '{target_file}' not found in data directory.")
             return
    else:
        pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found to process.")
        return

    print(f"Found {len(pdf_files)} book(s) to process.")
    
    for pdf_file in pdf_files:
        file_path = os.path.join(DATA_DIR, pdf_file)
        book_id = os.path.splitext(pdf_file)[0]
        create_vector_db_for_book(file_path, book_id)

    print("\n--- Data ingestion complete. ---")

if __name__ == "__main__":
    # Set up argument parser to handle command-line arguments
    parser = argparse.ArgumentParser(description="Process PDF books into a vector store.")
    parser.add_argument("--file", type=str, help="The specific filename of the book to process in the 'data' directory.")
    
    args = parser.parse_args()
    
    # Run the pipeline with the specific file if provided, otherwise run for all files.
    run_ingestion_pipeline(target_file=args.file)
