from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from eurospark.agent.state import GraphState
from eurospark.agent.tools import execute_sql, plot_chart, get_schema
from eurospark.agent.prompts import SYSTEM_PROMPT
from eurospark.config import settings

llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=settings.openai_api_key, temperature=0, streaming=True)
llm_with_tools = llm.bind_tools([execute_sql, plot_chart, get_schema])

def router_node(state: GraphState) -> GraphState:
    """Classifies the query and fetches schema context."""
    messages = state["messages"]
    schema = get_schema.invoke({})
    system = SystemMessage(content=SYSTEM_PROMPT.format(schema=schema))
    response = llm_with_tools.invoke([system] + messages)
    return {"messages": [response], "schema_context": schema}

def sql_node(state: GraphState) -> GraphState:
    """Executes tool calls from the LLM (SQL queries and chart rendering)."""
    from langchain_core.messages import ToolMessage
    last_msg = state["messages"][-1]
    tool_results = []
    sql_result = None
    chart_b64 = None
    
    for call in last_msg.tool_calls:
        if call["name"] == "execute_sql":
            result = execute_sql.invoke(call["args"])
            sql_result = result
        elif call["name"] == "plot_chart":
            result = plot_chart.invoke(call["args"])
            chart_b64 = result
        else:
            result = get_schema.invoke(call["args"])
        tool_results.append(ToolMessage(content=result, tool_call_id=call["id"]))
    
    return {"messages": tool_results, "sql_result": sql_result, "chart_base64": chart_b64}

def responder_node(state: GraphState) -> GraphState:
    """Synthesises a final natural-language answer from tool results."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}