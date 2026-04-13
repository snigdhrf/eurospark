from langgraph.graph import StateGraph, END
from eurospark.agent.state import GraphState
from eurospark.agent.nodes import router_node, sql_node, responder_node


def route_after_router(state: GraphState) -> str:
    """Decides next node based on whether LLM called a tool."""
    last_msg = state["messages"][-1]

    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "sql_node"

    return "responder"


def build_graph():
    graph = StateGraph(GraphState)

    # Nodes
    graph.add_node("router", router_node)
    graph.add_node("sql_node", sql_node)
    graph.add_node("responder", responder_node)

    # Entry point
    graph.set_entry_point("router")

    # Conditional routing
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "sql_node": "sql_node",
            "responder": "responder",
        },
    )

    # Flow
    graph.add_edge("sql_node", "responder")
    graph.add_edge("responder", END)

    return graph.compile()


# This is what your server imports
graph = build_graph()