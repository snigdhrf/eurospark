from langchain_core.tools import tool
from supabase import create_client
import plotly.express as px
import pandas as pd
import base64, json, io
from eurospark.config import settings

sb = create_client(settings.supabase_url, settings.supabase_key)

def execute_sql(query: str) -> str:
    """Executes a read-only SQL query against the eurospark schema. Returns JSON results."""
    # ✅ remove trailing semicolons (and whitespace)
    query = query.strip().rstrip(";")

    result = sb.rpc("execute_readonly_sql", {"query": query}).execute()
    return json.dumps(result.data)