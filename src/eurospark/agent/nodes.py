from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from eurospark.agent.state import GraphState
from eurospark.config import settings
from pydantic import BaseModel, Field
from typing import Literal
from supabase import create_client
import base64, json, io
from eurospark.config import settings
import plotly.express as px

from eurospark.agent.tools import execute_sql
from eurospark.agent.prompts import SUPERVISOR_PROMPT, SQL_AGENT_PROMPT, CHART_AGENT_PROMPT, RESPONDER_PROMPT, CLARIFICATION_AGENT_PROMPT

llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=settings.openai_api_key, temperature=0, streaming=True)

# SUPERVISOR
class SupervisorDecision(BaseModel):
    reasoning: str = Field(
        description = "In maximum 3 sentences, think about what task needs to be solved next.")
    next: Literal["responder", "sql_agent", "chart_agent", "user_clarification"]   # The llm will choice one of these options, this will set 'next_node' in the state
    queue_responder: bool = Field(
      default=False,
      description="Set to True when the task you just selected will give the responder everything it needs to answer the user. Set to False when more tasks are needed first (e.g. a chart still needs to be made after SQL)."
  )

llm_supervisor = llm.with_structured_output(SupervisorDecision)

def supervisor_node(state: GraphState) -> GraphState:
    messages = state["messages"]
    system_prompt = SystemMessage(content=SUPERVISOR_PROMPT)
    decision = llm_supervisor.invoke([system_prompt] + messages)
    return {"next_node": decision.next, "queue_responder": decision.queue_responder}


# RESPONDER
def responder_agent(state: GraphState) -> GraphState:
    """Synthesises a final natural-language answer from tool results."""
    messages = state["messages"]

    # if there is a result from a data query in the state, we will give the responder the FULL results here instead of only the preview
    if state["sql_result"]:
        sql_result = state["sql_result"]
        # inject full data temporarily so LLM can see everything
        data_context = AIMessage(content=f"Full query results:\n{sql_result}")
        messages = messages + [data_context]

    system_prompt = SystemMessage(content=RESPONDER_PROMPT)
    response = llm.invoke([system_prompt] + messages)
    return {"messages": [response]}


#SQL AGENT
class SQLquery(BaseModel):
    reasoning: str = Field(
        description = "In maximum 2 sentences, think about what querry would give the best and most relevant results needed.")
    query: str
    summary: str = Field(
          description="One sentence describing what this query retrieves in plain English.")
    
llm_sql = llm.with_structured_output(SQLquery)

def sql_agent(state: GraphState) -> GraphState:
    messages = state["messages"]

    current_schema = state["schema_context"]
    formatted_system_prompt = SQL_AGENT_PROMPT.format(schema=current_schema) # Inject shcmae into the SQL prompt string
    system_prompt = SystemMessage(content=formatted_system_prompt)

    result = llm_sql.invoke([system_prompt] + messages)
    query = result.query

    try:
        query_result = execute_sql(query)
        
        data = json.loads(query_result)
        preview = json.dumps(data[:5], indent=2)   # we only preview the first 5 rows of the results here
        query_message = AIMessage(content=f"SQL query completed:{result.summary}\n\nPreview of the result:\n{preview}\n")

        return {"sql_result": query_result, "messages": [query_message]}
    
    except Exception as e:
        message = AIMessage(content=f"SQL_FAILED\n\nError: '{str(e)}'\nQuery attempted: {result.query}")
        return {"sql_result": None, "messages": [message]}


#CHART AGENT
class ChartDecision(BaseModel):
      reasoning: str = Field(
          description="In 1-2 sentences, explain why you chose this chart type and these columns")
      chart_type: Literal["bar", "line", "scatter"] = Field(
          description="The type of chart to render")
      x_col: str = Field(
          description="Column name for the x-axis, must exactly match a column in the query results")
      y_col: str = Field(
          description="Column name for the y-axis, must exactly match a column in the query results")
      title: str = Field(
          description="A concise descriptive title for the chart")
      
llm_chart = llm.with_structured_output(ChartDecision)

def chart_agent(state: GraphState) -> GraphState:
    messages = state["messages"]
    sql_result = state["sql_result"]
    df = pd.DataFrame(json.loads(sql_result))

    # inject full data temporarily so LLM can see all column names
    data_context = AIMessage(content=f"Full query results to visualize:\n{sql_result}")
    augmented_messages = messages + [data_context]
    
    system_prompt = SystemMessage(content=CHART_AGENT_PROMPT)
    decision = llm_chart.invoke([system_prompt] + augmented_messages)

    try:
        fig_fns = {"bar": px.bar, "line": px.line, "scatter": px.scatter}
        fig = fig_fns.get(decision.chart_type, px.bar)(df, x=decision.x_col, y=decision.y_col,title=decision.title, template="plotly_white")
        buf = io.BytesIO()
        fig.write_image(buf, format="png", width=800, height=400)
        chart_base64 = base64.b64encode(buf.getvalue()).decode()

        chart_message = AIMessage(content=f"Chart generated and saved: {decision.title}")
        return {"chart_base64": chart_base64, "messages": [chart_message]}

    except Exception as e:
        error_message = AIMessage(content=f"CHART_FAILED\n\nError: {str(e)}\nColumns available:{list(df.columns)}")
        return {"chart_base64": None, "messages": [error_message]}
    

# CLARIFICATION AGENT
def clarification_node(state: GraphState) -> GraphState:
      messages = state["messages"][-3:]  # pass the last 3 messages of the conversation, this should be more than enough to contain the last user message
      system_prompt = SystemMessage(content=CLARIFICATION_AGENT_PROMPT)
      question = llm.invoke([system_prompt] + messages)
      #user_response = interrupt(question.content)  # pauses here, user_response gets the reply, we do not need an interupt, since the clarifiaction node will always be followed by the graph END

      return {"messages": [question]}  # this ads both the AI clarification question to messages


#SCHAME INJECTION NODE
sb = create_client(settings.supabase_url, settings.supabase_key)

def schema_node(state: GraphState) -> GraphState:
    schema = sb.rpc("get_eurospark_schema", {}).execute()
    schema = json.dumps(schema.data, indent=2)
    
    return {"schema_context": schema}