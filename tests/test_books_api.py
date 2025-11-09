import os
import shutil
import sys
from fastapi.testclient import TestClient
import pytest

# Add the project root to the system path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backend.main import app

# --- TEST SETUP AND TEARDOWN ---

# Use a test-specific directory for vector stores
TEST_VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), 'test_vector_store')

# Monkeypatch the VECTOR_STORE_DIR in the books API module
import src.backend.api.books as books_api
books_api.VECTOR_STORE_DIR = TEST_VECTOR_STORE_DIR

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    """Fixture to create and clean up the test vector store directory."""
    # Setup: ensure the test directory is clean before tests
    if os.path.exists(TEST_VECTOR_STORE_DIR):
        shutil.rmtree(TEST_VECTOR_STORE_DIR)
    os.makedirs(TEST_VECTOR_STORE_DIR)

    yield # This is where the tests will run

    # Teardown: remove the test directory after tests are done
    shutil.rmtree(TEST_VECTOR_STORE_DIR)

# --- TEST CASES ---

def test_list_books_with_no_books():
    """
    Test the /list endpoint when there are no books (or vector stores).
    """
    response = client.get("/api/v1/books/list")
    assert response.status_code == 200
    assert response.json() == {"books": []}

def test_list_books_with_valid_and_empty_dirs():
    """
    Test the /list endpoint's ability to correctly identify valid book directories
    and ignore invalid or empty ones.
    """
    # Create a valid "book" directory with a dummy file
    valid_book_dir = os.path.join(TEST_VECTOR_STORE_DIR, "correct_book")
    os.makedirs(valid_book_dir)
    with open(os.path.join(valid_book_dir, "index.faiss"), "w") as f:
        f.write("dummy index")

    # Create an empty directory to simulate a failed ingestion
    empty_book_dir = os.path.join(TEST_VECTOR_STORE_DIR, "failed_ingestion")
    os.makedirs(empty_book_dir)

    # Create a file that should be ignored
    ignored_file = os.path.join(TEST_VECTOR_STORE_DIR, "should_be_ignored.txt")
    with open(ignored_file, "w") as f:
        f.write("I am not a book directory.")

    # --- THE BUG ---
    # The current implementation incorrectly includes "failed_ingestion"
    # because it only checks if a path is a directory.

    # Make the API call
    response = client.get("/api/v1/books/list")

    # --- VERIFICATION ---
    assert response.status_code == 200
    response_data = response.json()

    # The response should ONLY contain the valid book
    assert "correct_book" in response_data["books"]

    # This assertion will fail with the current buggy implementation
    assert "failed_ingestion" not in response_data["books"]

    # The final list should only have one book
    assert len(response_data["books"]) == 1
