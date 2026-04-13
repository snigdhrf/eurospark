from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from eurospark.agent.state import GraphState
from eurospark.agent.nodes import router_node, sql_node, responder_node

def route_after_router(state: GraphState) -> str:
    """Conditional edge: decides next node based on whether LLM called a tool."""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "sql_node"     # LLM wants to run SQL or plot
    return "responder"        # LLM answered directly (no tools needed)

def build_graph(checkpointer=None):
    graph = StateGraph(GraphState)
    
    graph.add_node("router", router_node)
    graph.add_node("sql_node", sql_node)
    graph.add_node("responder", responder_node)
    
    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_after_router, {
        "sql_node": "sql_node",
        "responder": "responder",
    })
    graph.add_edge("sql_node", "responder")
    graph.add_edge("responder", END)
    
    # memory = checkpointer or MemorySaver()
    # return graph.compile(checkpointer=memory)

    return graph.compile()

graph = build_graph()   # LangGraph Server imports this