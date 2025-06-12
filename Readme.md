# **AI Programming Book Tutor**

This is a full-stack application that allows users to chat with their programming books. It leverages a sophisticated multi-agent system built with LangGraph to provide intelligent, context-aware answers. The backend is powered by FastAPI, and the interactive user interface is built with Streamlit.

## **✨ Features**

* **Intelligent Agentic Workflow**: The system uses a LangGraph-powered "Triage" workflow. An agent first analyzes the user's intent before deciding whether to consult the book, search the web, or answer from its own knowledge.  
* **Retrieval-Augmented Generation (RAG)**: Ingests one or more PDF books into a FAISS vector store, allowing the AI to find and cite information directly from the source material.  
* **Persistent Chat History**: Saves conversation history for each book session in a local SQLite database, so you can pick up where you left off, even after restarting the app.  
* **Dynamic Book Management**: Users can upload new PDF books directly through the web interface. The application automatically processes and vectorizes them, making them instantly available for study sessions.  
* **Live Web Search**: If a question cannot be answered by the book or the model's internal knowledge, the agent can perform a real-time web search using the Serper API.

## **⚙️ System Architecture**

The application is built on a decoupled frontend and backend architecture.

1. **Frontend (Streamlit)**: A simple, interactive web interface that allows users to upload and select books, and chat with the AI tutor.  
2. **Backend (FastAPI)**: A robust API server that exposes the agentic workflow. It handles chat logic, file uploads, and database interactions.  
3. **Agentic Core (LangGraph)**: The "brain" of the application. It manages the state and flow of conversation between different agents (Router, Book Retriever, Web Searcher, and Final Answer Generator).  
4. **Database (SQLite)**: A single-file database for persisting chat histories across different sessions and books.  
5. **Vector Store (FAISS)**: A directory of FAISS indexes, with a separate, dedicated index created for each uploaded book.

## **🚀 Setup and Installation Guide**

Follow these steps carefully to set up and run the project on your local machine.

### **1\. Prerequisites**

* Python 3.9 or higher  
* Git installed on your system

### **2\. Clone the Repository**

Open your terminal and clone the GitHub repository to your local machine.

git clone https://github.com/shahedmomenzadeh/Book\_assistant.git  
cd Book\_assistant

### **3\. Create a Virtual Environment**

It is highly recommended to use a virtual environment to manage project dependencies.

**On macOS / Linux:**

python3 \-m venv venv  
source venv/bin/activate

**On Windows:**

python \-m venv venv  
.\\venv\\Scripts\\activate

### **4\. Set Up API Keys**

Your API keys should be kept secret and should not be committed to version control.

**a.** Create a file named .env in the root directory of the project.

**b.** Add your secret keys to the .env file in the following format:

\# Get your key from Google AI Studio: https://aistudio.google.com/app/apikey  
GOOGLE\_API\_KEY="your\_google\_api\_key\_here"

\# Get your key from Serper.dev  
SERPER\_API\_KEY="your\_serper\_api\_key\_here"

### **5\. Install Dependencies**

Install all the required Python packages using the requirements.txt file.

pip install \-r requirements.txt

## **▶️ Running the Application**

To run the application, you need to start the backend and frontend servers in two separate terminal windows.

### **Step 1: Ingest Initial Books (Optional)**

If you have any PDF books you want to be available from the start, place them inside the data/ directory. Then, run the ingestion script from the project root:

python scripts/ingest\_book.py

This will process all books in the data folder. You can also upload books later through the user interface.

### **Step 2: Start the Backend Server**

In your first terminal (with the virtual environment activated), start the FastAPI server.

uvicorn src.backend.main:app \--reload \--port 8000

You should see output indicating that the Uvicorn server is running. The backend is now live at http://localhost:8000.

### **Step 3: Start the Frontend Server**

Open a **second terminal window**, navigate to the same project directory, and activate the virtual environment again. Then, start the Streamlit server.

streamlit run src/frontend/app.py

A new tab should automatically open in your web browser pointing to http://localhost:8501.

### **Step 4: Use the App\!**

You can now use the application:

1. **Upload a Book**: Use the file uploader in the sidebar to add a new PDF.  
2. **Select a Book**: Choose a book from the dropdown menu to start a chat session.  
3. **Chat**: Ask questions\! Try simple greetings, technical questions from the book, and questions that might require a web search to see how the agent responds.

## **📂 Project Structure**

Book\_assistant/  
│  
├── .env                  \# Stores secret API keys (you must create this)  
├── .gitignore            \# Specifies files for Git to ignore  
├── requirements.txt      \# Lists all Python dependencies  
├── chat\_history.db       \# SQLite database for chat history (created on first run)  
│  
├── data/                 \# Place initial PDF books here  
├── notebooks/            \# Jupyter notebooks for testing and visualization  
├── scripts/              \# Contains the ingestion script  
├── src/                  \# Main source code directory  
│   ├── backend/  
│   │   ├── api/  
│   │   ├── core/  
│   │   └── schemas/  
│   └── frontend/  
│       └── app.py  
│  
└── vector\_store/         \# Stores the generated FAISS indexes for each book  
