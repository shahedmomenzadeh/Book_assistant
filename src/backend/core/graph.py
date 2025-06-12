from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from .agents import AgentState, agent_router, book_retriever_node, web_search_node, generate_final_answer_node

# --- 1. Define the Graph ---
workflow = StateGraph(AgentState)

# --- 2. Add Nodes to the Graph ---
workflow.add_node("agent", agent_router)
workflow.add_node("book_retriever", book_retriever_node)
workflow.add_node("web_search", web_search_node)
workflow.add_node("generate_final_answer", generate_final_answer_node)

# --- 3. Add Edges to the Graph ---
workflow.set_entry_point("agent")

# Add conditional edge from the router
workflow.add_conditional_edges(
    "agent",
    lambda state: state["next"],
    {
        # The keys here MUST match the 'name' of the tools
        "BookRetrieverTool": "book_retriever",
        "google_serper": "web_search", # Corrected from "GoogleSerperRun"
        "generate_final_answer": "generate_final_answer"
    }
)

# After tool nodes run, they loop back to the agent to process the output
workflow.add_edge("book_retriever", "agent")
workflow.add_edge("web_search", "agent")

# The generation node is the final step, so it connects to the END
workflow.add_edge("generate_final_answer", END)


# --- 4. Compile the Graph ---
app = workflow.compile()

# --- Example Usage (for testing) ---
def run_example():
    """A simple function to test the compiled graph."""
    inputs = AgentState(
        question="search the Internet: Implementation of GAN in Pytorch. give me a complete code.",
        book_id="David Foster - Generative Deep Learning_ Teaching Machines To Paint, Write, Compose, and Play (2023, O'Reilly Media) - libgen.li",
        messages=[HumanMessage(content="search the Internet: Implementation of GAN in Pytorch. give me a complete code.")]
    )
    # Stream the outputs from the graph
    for output in app.stream(inputs, {'recursion_limit': 10}):
        # The output is a dictionary where keys are node names
        for key, value in output.items():
            print(f"Output from node '{key}':")
            print("---")
            print(value)
        print("\n---\n")

# To run this example from the project root:
# python -c "from src.backend.core.graph import run_example; run_example()"
