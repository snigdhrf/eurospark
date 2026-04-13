from fastapi import FastAPI
from langgraph.graph import CompiledGraph

# import your graph
from src.eurospark.agent.graph import graph

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

# minimal test endpoint
@app.post("/run")
async def run_graph(input_data: dict):
    result = await graph.ainvoke(input_data)
    return result