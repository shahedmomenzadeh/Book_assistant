import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Construct the path to the .env file which should be in the project root
# This allows the settings to be loaded regardless of where the script is run from.
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    """
    Pydantic settings class to manage environment variables.
    It automatically reads variables from the .env file.
    """
    # Google API Key for Generative AI services (Gemini, Embeddings)
    GOOGLE_API_KEY: str

    # Serper API Key for the web search tool.
    SERPER_API_KEY: str

    # Define the model names we will use throughout the application
    # This makes it easy to update models in one place.
    EMBEDDING_MODEL: str = "models/embedding-001"
    LLM_MODEL: str = "gemini-2.5-flash-preview-05-20"

    # Define paths for data and vector store for consistency
    # CORRECTED PATH: Goes up three levels from src/backend/core to the project root.
    DB_FAISS_PATH: str = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'vector_store')
    
    class Config:
        # Pydantic configuration to read from a .env file
        case_sensitive = True
        env_file = env_path
        env_file_encoding = 'utf-8'

# Create a single, reusable instance of the settings
settings = Settings()
