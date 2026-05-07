from langgraph.graph import StateGraph, END
from eurospark.agent.state import GraphState
from langgraph.checkpoint.memory import MemorySaver

from eurospark.agent.nodes import schema_node, supervisor_node, sql_agent, chart_agent, responder_agent, clarification_node

# conditional functions to define that conditional edges
def supervisor_routing(state: GraphState) -> str:
    """returns next node chosen by the supervisor"""

    print(state["next_node"])
    return state["next_node"]


def routing_back_to_supervisor(state: GraphState) -> str:
    """Conditional edge after the SQL agent, it loops back to the supervisor UNLESS queue_responder = TRUE, in case of an ERROR cath we also go to supervisor"""
    last_message = state["messages"][-1]
    if last_message.content.startswith(("SQL_FAILED", "CHART_FAILED")): # Catching ERROR messages from the SQL and from the chart agents
        return "supervisor"
    elif state["queue_responder"]:
        return "responder"
    else:
        return "supervisor"


def build_graph():
    graph = StateGraph(GraphState)

    # Nodes
    graph.add_node("schema_node", schema_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("sql_node", sql_agent)
    graph.add_node("chart_node", chart_agent)
    graph.add_node("responder_node", responder_agent)
    graph.add_node("clarification_node", clarification_node)

    # Entry point
    graph.set_entry_point("schema_node")
    graph.add_edge("schema_node", "supervisor")

    # Conditional routing by supervisor
    graph.add_conditional_edges(
        "supervisor",
        supervisor_routing,
        {
            "responder": "responder_node",
            "sql_agent": "sql_node",
            "chart_agent": "chart_node",
            "user_clarification": "clarification_node"
        },
    )

    # Conditional routing the sql back to the supervisor
    graph.add_conditional_edges(
        "sql_node",
        routing_back_to_supervisor,
        {
            "supervisor": "supervisor",
            "responder": "responder_node"
        },
    )

    # Conditional routing the chart node back to the supervisor
    graph.add_conditional_edges(
        "chart_node",
        routing_back_to_supervisor,
        {
            "supervisor": "supervisor",
            "responder": "responder_node"
        },
    )

    graph.add_edge("responder_node", END)
    graph.add_edge("clarification_node", END) # in the current design the clarification node HAS TO ALWAYS go to the END, because its here that we get user input without and interupt

    checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)

# This is what the server imports
graph = build_graph()