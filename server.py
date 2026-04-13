from langgraph.graph import StateGraph
from fastapi import FastAPI
from langgraph_api import add_routes

# import your graph
from src.eurospark.agent.graph import graph

app = FastAPI()

add_routes(app, graph, path="/")