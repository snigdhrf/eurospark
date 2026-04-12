from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    sql_result: str | None       # raw query result
    chart_base64: str | None     # plotly chart as base64 PNG
    schema_context: str | None   # table schemas injected into prompt
    query_type: str | None       # 'sql', 'viz', or 'direct'