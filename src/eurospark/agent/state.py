from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_node: str | None
    sql_result: str | None       # raw query result
    chart_base64: str | None     # plotly chart as base64 PNG
    schema_context: str | None   # table schemas injected into prompt
    queue_responder: bool # lets the supervisor skip himself after the next task is complete and instead let the responder handle the users question
    #query_type: str | None       # 'sql', 'viz', or 'direct'

# this state is used in the 'build_graph' in order to ensure that the default input is allowed to be a state containing only a message
# this will make it so the other inputs are no longer required and will allowed to just be empty
class InputState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]