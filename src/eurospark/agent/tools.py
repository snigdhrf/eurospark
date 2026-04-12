from langchain_core.tools import tool
from supabase import create_client
import plotly.express as px
import pandas as pd
import base64, json, io
from eurospark.config import settings

sb = create_client(settings.supabase_url, settings.supabase_key)

@tool
def get_schema() -> str:
    """Returns the database schema so the agent knows what tables and columns exist."""
    result = sb.rpc("get_eurospark_schema", {}).execute()
    return json.dumps(result.data, indent=2)

@tool
def execute_sql(query: str) -> str:
    """Executes a read-only SQL query against the eurospark schema. Returns JSON results."""
    result = sb.rpc("execute_readonly_sql", {"query": query}).execute()
    return json.dumps(result.data)

@tool
def plot_chart(data_json: str, chart_type: str, x_col: str, y_col: str, title: str) -> str:
    """Creates a Plotly chart from JSON data. Returns a base64-encoded PNG."""
    df = pd.DataFrame(json.loads(data_json))
    fig_fns = {"bar": px.bar, "line": px.line, "scatter": px.scatter}
    fig = fig_fns.get(chart_type, px.bar)(df, x=x_col, y=y_col, title=title, template="plotly_white")
    buf = io.BytesIO()
    fig.write_image(buf, format="png", width=800, height=400)
    return base64.b64encode(buf.getvalue()).decode()