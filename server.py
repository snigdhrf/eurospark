# load all api keys into os.env
from dotenv import load_dotenv
load_dotenv()


from fastapi import FastAPI

# import your graph
from eurospark.agent.graph import graph


app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/run")
async def run_graph(input_data: dict):
    result = await graph.ainvoke(input_data)
    return result