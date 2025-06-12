import os
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from .settings import settings

def get_retriever(book_id: str):
    """
    Creates and returns a FAISS retriever for a specific book.

    This function constructs the path to the book's vector store, loads it,
    and creates a retriever object that can be used to find relevant documents.

    Args:
        book_id (str): The unique identifier for the book.

    Returns:
        A LangChain retriever object configured for the specific book.
        Returns None if the vector store for the book does not exist.
    """
    # Construct the path to the specific book's vector store
    book_vector_store_path = os.path.join(settings.DB_FAISS_PATH, book_id)

    if not os.path.exists(book_vector_store_path):
        print(f"Vector store for book '{book_id}' not found at {book_vector_store_path}.")
        # In a real app, you might raise a specific HTTP exception here.
        return None

    # Initialize the embedding model specified in our settings
    embeddings = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL)

    # Load the FAISS vector store from the local path
    db = FAISS.load_local(
        folder_path=book_vector_store_path, 
        embeddings=embeddings,
        allow_dangerous_deserialization=True # Required for loading local FAISS index
    )

    # Convert the vector store into a retriever object
    # 'k=4' means it will retrieve the top 4 most relevant documents
    retriever = db.as_retriever(search_kwargs={'k': 4})
    
    return retriever

