# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EuroSpark is a LangGraph ReAct agent that answers natural-language questions about European electricity markets by querying a Supabase PostgreSQL database and returning interactive Plotly charts.

## Development Commands

### Install dependencies
```bash
pip install uv
uv pip install --system -e ".[dev,frontend,data]"
```

### Run the agent backend (LangGraph Server)
```bash
langgraph up --port 2024 --no-browser
# Available at http://localhost:2024 + LangGraph Studio UI
```

### Run the frontend
```bash
streamlit run frontend/app.py
# Available at http://localhost:8501
```

### Seed the database
```bash
# Step 1: Run src/eurospark/db/schema.sql manually in Supabase SQL Editor
# Step 2: Load CSV data
python -m src.eurospark.db.seed
```

### Run tests
```bash
pytest tests/ -v
```

### Docker
```bash
docker build -t eurospark .
docker run -p 10000:10000 -e OPENAI_API_KEY=... eurospark
```

## Environment Variables

Defined via Pydantic Settings in `src/eurospark/config.py`. Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key (uses GPT-4o-mini) |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon key |
| `SUPABASE_DB_URL` | Yes | PostgreSQL connection string (port 6543) |
| `DATABASE_URI` | No | Render PostgreSQL for `PostgresSaver` in production |
| `LANGSMITH_API_KEY` | No | LangSmith tracing |
| `LANGSMITH_TRACING` | No | Enable tracing (default: False) |

## Architecture

### Agent Graph (`src/eurospark/agent/`)

The core is a 3-node `StateGraph` (`graph.py`):

```
router_node → (conditional) → sql_node → responder_node → END
                    ↓ (no tool calls)
              responder_node → END
```

- **`router_node`** (`nodes.py`): Fetches DB schema, injects it into the system prompt (`prompts.py`), calls GPT-4o-mini with tools bound. If the LLM decides to call tools, the message will have `tool_calls`.
- **`sql_node`** (`nodes.py`): Iterates over `tool_calls` and dispatches to the three tools in `tools.py`. Wraps results as `ToolMessage` objects.
- **`responder_node`** (`nodes.py`): Final LLM call that synthesizes a natural-language answer from tool results.

**State** (`state.py`): `GraphState` TypedDict with `messages` (uses `add_messages` reducer), `sql_result`, `chart_base64`, `schema_context`, `query_type`.

**Tools** (`tools.py`):
- `get_schema()` — returns JSON of table/column names from Supabase
- `execute_sql(query)` — runs queries through the `execute_readonly_sql` PL/pgSQL function (SELECT-only, 1000-row limit)
- `plot_chart(data_json, chart_type, x_col, y_col, title)` — renders a Plotly chart and returns it as base64 PNG

### Database (`src/eurospark/db/`)

Three tables in the `eurospark` Postgres schema (data 2015–2023):
- `electricity_prices` — household & industrial prices (EUR/kWh) by country/year
- `renewable_capacity` — wind/solar/hydro capacity (GW) + share (%)
- `energy_consumption` — consumption by sector (Mtoe)

All SQL queries are enforced as read-only via `execute_readonly_sql` stored procedure. Raw CSV data lives in `data/`.

### Frontend (`frontend/app.py`)

Streamlit chat UI. Posts messages to the backend `POST /run` endpoint (defined in `server.py`), streams responses via SSE, and renders base64-encoded Plotly charts inline.

### LangGraph Server Config (`langgraph.json`)

Registers the graph at `src/eurospark/agent/graph.py:graph` as the `eurospark` graph. The server exposes a REST + SSE API used by the frontend.

## Deployment

- **Backend**: Render (free tier Docker container, port 10000)
- **Frontend**: Streamlit Cloud (free tier, reads env secrets)
- **Database**: Supabase free tier
- **Persistent thread memory**: `PostgresSaver` (Render PostgreSQL add-on) in production; `MemorySaver` in local dev
