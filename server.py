from fastapi import FastAPI
from langgraph_api.server import create_app

# This automatically reads langgraph.json
app: FastAPI = create_app()