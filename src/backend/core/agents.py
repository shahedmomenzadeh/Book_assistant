import os
import operator
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
# Use the Pydantic v1 compatibility namespace as recommended by the warning
from pydantic.v1 import BaseModel, Field 
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.tools import GoogleSerperRun
from langchain_google_genai import ChatGoogleGenerativeAI

from .settings import settings
from .rag import get_retriever

# --- 1. Define the Tools our Agents can use ---

serper_api_wrapper = GoogleSerperAPIWrapper(serper_api_key=settings.SERPER_API_KEY)
# Give the search tool a very explicit description to help the router.
web_search_tool = GoogleSerperRun(
    api_wrapper=serper_api_wrapper,
    description="A search engine. Use this to search the internet for real-time information, such as weather, news, or current events, or for topics not found in the book."
)


class BookRetrieverTool(BaseModel):
    """Tool for looking up relevant information from a specific programming book."""
    query: str = Field(description="The query or question to look up in the book.")

    def run(self, book_id: str):
        """Executes the book retrieval, injecting the book_id from the state."""
        retriever = get_retriever(book_id)
        if not retriever:
            return f"Error: Could not find or load the vector store for book_id '{book_id}'."
        
        docs = retriever.invoke(self.query)
        if not docs:
            return "No relevant information found in the book for this query."
        return "\n\n".join([f"Source: {doc.metadata.get('source', 'N/A')}, Page: {doc.metadata.get('page', 'N/A')}\nContent: {doc.page_content}" for doc in docs])

# --- 2. Define the State for our Graph ---

class AgentState(TypedDict):
    """The shared memory that flows through the graph."""
    question: str
    book_id: str
    messages: Annotated[List[BaseMessage], operator.add]
    next: str

# --- 3. Define the Agent Nodes with Refactored Prompts ---

ROUTER_SYSTEM_PROMPT = """You are an expert AI agent that acts as a router. Your only job is to decide the next step in a workflow. Do not answer the user's question directly.

You have these tools available:
- `BookRetrieverTool`: Use this for questions about the content of a specific book.
- `google_serper`: Use this for questions that require real-time information or a web search (e.g., weather, news, current events).

**Your Decision Process:**

1.  **Examine the user's latest message.**
2.  **If the message is a greeting, thank you, or simple conversational filler**, route to `generate_final_answer`.
3.  **If the message is a question that requires a web search for real-time information**, you MUST call the `google_serper` tool.
4.  **For any other question**, you MUST assume it is about the book and call the `BookRetrieverTool` as the first step.
5.  **After a tool has run**, look at the new information.
    - If the information is sufficient to answer the question, route to `generate_final_answer`.
    - If the `BookRetrieverTool` found nothing, you MUST call the `google_serper` tool to try and find the answer online.

Choose the single best tool or the `generate_final_answer` step.
"""

FINAL_ANSWER_SYSTEM_PROMPT = """You are an expert AI programming assistant generating a final answer. The conversation history may contain context from a book, a web search, or neither.

-   If the history contains book context, use it as your primary source and cite the page number if available.
-   If the history contains web search context, synthesize it into your answer.
-   If the history contains no tool output (because the router sent the user here directly), you MUST answer from your own knowledge and state that the information is not from the provided book. For example: "I couldn't find a specific answer for that in the book, but here is a general explanation..."
-   If the input was simply conversational, provide a friendly, conversational response.
"""

llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, temperature=0)
llm_with_tools = llm.bind_tools([web_search_tool, BookRetrieverTool])

def agent_router(state: AgentState) -> dict:
    """
    The primary agent node. It analyzes intent and decides the next action.
    """
    print("---AGENT ROUTER (TRIAGE)---")
    messages_with_prompt = [SystemMessage(content=ROUTER_SYSTEM_PROMPT)] + state['messages']
    
    response = llm_with_tools.invoke(messages_with_prompt)
    
    if not response.tool_calls:
        print("-> Decision: No tool call needed. Proceeding to generate final answer.")
        return {"next": "generate_final_answer"}
    
    print(f"-> Decision: Call tool '{response.tool_calls[0]['name']}'.")
    return {"messages": [response], "next": response.tool_calls[0]['name']}

def generate_final_answer_node(state: AgentState) -> dict:
    """
    Generates the final response to the user using the dedicated final answer prompt.
    """
    print("---GENERATE FINAL ANSWER---")
    messages_with_prompt = [SystemMessage(content=FINAL_ANSWER_SYSTEM_PROMPT)] + state['messages']
    
    response = llm.invoke(messages_with_prompt)
    
    return {"messages": [response]}

def book_retriever_node(state: AgentState) -> dict:
    """Executes the book retrieval tool."""
    print("---BOOK RETRIEVER---")
    tool_call = state['messages'][-1].tool_calls[0]
    tool = BookRetrieverTool(query=tool_call['args']['query'])
    result = tool.run(book_id=state['book_id'])
    return {"messages": [ToolMessage(content=result, tool_call_id=tool_call['id'])]}

def web_search_node(state: AgentState) -> dict:
    """Executes the web search tool."""
    print("---WEB SEARCH---")
    tool_call = state['messages'][-1].tool_calls[0]
    # The tool should be invoked with the entire arguments dictionary,
    # not just the extracted query string.
    result = web_search_tool.invoke(tool_call['args'])
    return {"messages": [ToolMessage(content=result, tool_call_id=tool_call['id'])]}
