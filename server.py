from fastapi import FastAPI

# import your graph
from src.eurospark.agent.graph import graph

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

# Accepts JSON body → automatically parsed as input_data
@app.post("/run")
async def run_graph(input_data: dict):
    result = await graph.ainvoke(input_data)
    return result