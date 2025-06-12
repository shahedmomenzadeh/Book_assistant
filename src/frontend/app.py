import streamlit as st
import requests
import json
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Programming Book Tutor",
    page_icon="�",
    layout="wide"
)

# --- Constants ---
API_BASE_URL = "http://localhost:8000/api/v1"
CHAT_API_URL = f"{API_BASE_URL}/chat"
UPLOAD_API_URL = f"{API_BASE_URL}/books/upload"
LIST_BOOKS_API_URL = f"{API_BASE_URL}/books/list"
HISTORY_API_URL = f"{API_BASE_URL}/history" # Endpoint to get chat history

# --- Helper Functions ---
@st.cache_data(ttl=60)
def get_available_books():
    """
    Fetches the list of available books from the backend API.
    """
    try:
        response = requests.get(LIST_BOOKS_API_URL)
        response.raise_for_status()
        return response.json().get("books", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Could not fetch book list: {e}")
        return []

def get_chat_history(session_id: str):
    """
    Fetches the persistent chat history for a session from the backend.
    """
    try:
        response = requests.get(f"{HISTORY_API_URL}/{session_id}")
        response.raise_for_status()
        return response.json().get("history", [])
    except requests.exceptions.RequestException:
        # It's okay if history doesn't exist for a new session, return empty list
        return []

# --- Callback for File Uploader ---
def handle_file_upload():
    """
    This function is called ONCE when a new file is uploaded via the file_uploader.
    """
    if 'file_uploader_key' in st.session_state and st.session_state['file_uploader_key'] is not None:
        uploaded_file = st.session_state['file_uploader_key']
        with st.spinner(f"Processing '{uploaded_file.name}'... This may take a few minutes."):
            try:
                files = {'file': (uploaded_file.name, uploaded_file, 'application/pdf')}
                response = requests.post(UPLOAD_API_URL, files=files)
                
                if response.status_code == 200:
                    st.success(response.json().get("message", "Book processed successfully!"))
                    # Clear the data cache to force a refresh of the book list
                    st.cache_data.clear()
                    # A short sleep gives the user time to see the success message
                    time.sleep(2)
                else:
                    error_detail = response.json().get('detail', 'Unknown error')
                    st.error(f"Error uploading book: {error_detail}")

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to the backend: {e}")

# --- Main Application ---
st.title("📚 AI Programming Book Tutor")
st.caption("Chat with your programming books, powered by LangGraph and Gemini")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")

    st.header("Add a New Book")
    st.file_uploader(
        "Upload a PDF to begin ingestion",
        type="pdf",
        key='file_uploader_key',
        on_change=handle_file_upload
    )

    st.header("Select a Book")
    available_books = get_available_books()
    
    if not available_books:
        st.warning("No books found. Upload one to get started.")

    selected_book = st.selectbox(
        "Choose a book to study:",
        options=available_books,
        key="book_selector"
    )
    
    # Load persistent history when the book selection changes
    if 'current_book' not in st.session_state or st.session_state.current_book != selected_book:
        st.session_state.current_book = selected_book
        session_id = f"streamlit_session_{selected_book}"
        st.session_state.session_id = session_id
        # Load chat history from the backend for the selected book
        st.session_state.messages = get_chat_history(session_id)
        if selected_book:
            st.info(f"Switched to book: **{selected_book}**")

# --- Chat Interface ---
if not st.session_state.get('current_book'):
    st.info("Please select a book or upload a new one using the sidebar to begin chatting.")
    st.stop()

# Display previous chat messages from the session state
for message in st.session_state.get("messages", []):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle new chat input
if prompt := st.chat_input("Ask a question about the book..."):
    # Append the new user message to the session state for immediate display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream the response from the backend
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""
        try:
            payload = {
                "question": prompt,
                "book_id": st.session_state.current_book,
                "session_id": st.session_state.session_id
            }
            with requests.post(CHAT_API_URL, json=payload, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=None):
                    if chunk:
                        data_str = chunk.decode('utf-8')
                        if data_str.startswith('data: '):
                            json_str = data_str[len('data: '):]
                            try:
                                data = json.loads(json_str)
                                full_response += data.get("token", "")
                                response_container.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                pass
            response_container.markdown(full_response)
            # Append the final assistant response to the session state
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except requests.exceptions.RequestException as e:
            st.error(f"Error communicating with backend: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
