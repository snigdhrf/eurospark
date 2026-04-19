from fastapi import FastAPI, HTTPException
from src.eurospark.agent.graph import graph

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/run")
async def run_graph(input_data: dict):
    try:
        # ✅ Ensure full GraphState structure
        state = {
            "messages": input_data.get("messages", []),
            "sql_result": None,
            "chart_base64": None,
            "schema_context": None,
            "query_type": None,
        }

        # Run LangGraph
        result = await graph.ainvoke(state)

        # ✅ Extract last assistant message
        messages = result.get("messages", [])
        if not messages:
            raise ValueError("No messages returned from graph")

        last_msg = messages[-1]

        # Handle both dict and LangChain message object
        if hasattr(last_msg, "content"):
            content = last_msg.content
        else:
            content = last_msg.get("content", "")

        # ✅ Extract chart properly
        chart = result.get("chart_base64")

        # ✅ Clean API response (frontend-friendly)
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": content
                }
            ],
            "chart": chart
        }

    except Exception as e:
        print("ERROR:", str(e))
        raise HTTPException(status_code=500, detail=str(e))