# ⚡ EuroSpark - EU Energy Market Analytics Agent

> A production-deployed LangGraph ReAct agent that answers natural language questions
> about European electricity markets : querying a Supabase PostgreSQL database,
> generating SQL on the fly, and returning interactive Plotly charts.

<!-- [![CI](https://github.com/YOUR_USERNAME/eurospark/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/eurospark/actions) -->
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-purple.svg)](https://langchain-ai.github.io/langgraph/)

**[Live demo →](https://eurospark-frontend.onrender.com/)**  ·  **[LangGraph Server API →](https://eurospark-1.onrender.com)**

---

## What it does

Ask plain-English questions about EU energy data and get SQL-backed answers with charts:

```
"Which EU country had the cheapest household electricity in 2023?"
"Plot renewable energy share growth for France and Germany since 2015."
"How did the 2022 energy crisis affect industrial electricity prices?"
"Which sector consumes the most energy in Poland?"
```

The agent decides whether to query the database, generate a chart, or answer directly : 
all without any hand-coded routing logic.

---

## Architecture

```
User
 │
 ▼
Streamlit frontend (Streamlit Cloud — free)
 │  SSE streaming
 ▼
LangGraph Server API (Render — free)
 │
 ▼
┌─────────────────────────────────────────┐
│  StateGraph                             │
│                                         │
│  preprocess ──► agent ──► tools ──►─┐  │
│                  ▲                   │  │
│                  └───────────────────┘  │
│                  │ (no tools) ▼         │
│                 END                     │
└─────────────────────────────────────────┘
 │
 ▼
Supabase PostgreSQL (eurospark schema)
```

---

## LangGraph concepts demonstrated

| Concept | File | Notes |
|---|---|---|
| `StateGraph` | `graph.py` | Explicit typed graph, not `create_react_agent` |
| `TypedDict` state + `Annotated` reducers | `state.py` | `add_messages` for conversation history |
| Node functions | `nodes.py` | `preprocess`, `agent`, `tools` |
| Conditional edges | `graph.py` | `tools_condition` routes on tool_calls |
| Tool calling (`@tool`) | `tools.py` | `execute_sql`, `plot_chart`, `get_schema` |
| `MemorySaver` | `graph.py` | Local dev — in-process thread memory |
| `PostgresSaver` | `graph.py` | Production — persists threads across restarts |
| LangGraph Server | `langgraph.json`, `Dockerfile` | REST + SSE API, one-command deploy |
| Streaming (`astream_events`) | `frontend/app.py` | Token-by-token text + live chart delivery |
| LangSmith tracing | `config.py` + env | Full run traces, tool call visibility |

---

## Stack

| Layer | Technology | Cost |
|---|---|---|
| Agent framework | [LangGraph 0.2](https://langchain-ai.github.io/langgraph/) | Free |
| LLM | GPT-4o-mini | ~$0.001/query |
| Database | [Supabase](https://supabase.com) (PostgreSQL) | Free tier |
| Agent API | [LangGraph Server](https://langchain-ai.github.io/langgraph/concepts/langgraph_server/) on [Render](https://render.com) | Free tier |
| Frontend | [Streamlit](https://streamlit.io) | Free tier |
| Observability | [LangSmith](https://smith.langchain.com) | Free tier |
| CI | GitHub Actions | Free |

---

## Dataset

Eurostat-based data for **EU countries** , **2015–2023**:

| Table | Description | Rows |
|---|---|---|
| `eurospark.electricity_prices` | Household & industrial prices (EUR/kWh) | 180 |
| `eurospark.renewable_capacity` | Wind, solar, hydro capacity (GW) + share (%) | 360 |
| `eurospark.energy_consumption` | Consumption by sector (Mtoe) | 360 |

---

## Local setup (5 commands)

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USERNAME/eurospark && cd eurospark
pip install uv && uv pip install --system -e ".[dev,frontend,data]"

# 2. Configure credentials
cp .env.example .env
# → Fill in OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY, SUPABASE_DB_URL

# 3. Seed the database (run schema.sql in Supabase first)
make seed

# 4. Start the LangGraph agent server (+ LangGraph Studio)
make dev         # runs on http://localhost:2024

# 5. In a second terminal, start the Streamlit frontend
streamlit run frontend/app.py
```

---

## Supabase setup

1. Create a free project at [supabase.com](https://supabase.com).
2. Open the SQL Editor and paste the contents of `src/eurospark/db/schema.sql`.
3. Run it — this creates tables, RLS policies, and helper functions.
4. Copy your credentials into `.env`:
   - **SUPABASE_URL** → Settings > API > Project URL
   - **SUPABASE_KEY** → Settings > API > anon public key
   - **SUPABASE_DB_URL** → Settings > Database > Connection string (URI, port 6543)
5. Run `make seed` to load the CSV data.

---

## Deploy to Render (free)

1. Push this repo to GitHub.
2. [render.com](https://render.com) → New → Web Service → connect your repo.
3. **Runtime**: Docker. Render will use the `Dockerfile` automatically.
4. Add environment variables: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`,
   `SUPABASE_DB_URL`, `LANGSMITH_API_KEY`, `LANGSMITH_TRACING=true`.
5. Add a free **PostgreSQL add-on** on Render → set `DATABASE_URI` to its URL
   (used by `PostgresSaver` for persistent thread memory).
6. Deploy. Auto-deploys on every push to `main`.

---

## Deploy frontend to Streamlit Cloud

1. [streamlit.io](https://streamlit.io) → New app → connect GitHub.
2. Main file: `frontend/app.py`.
3. Requirements file: `frontend/requirements.txt`.
4. Secrets → add `LANGGRAPH_URL = "https://your-service.onrender.com"`.

---

## Running tests

```bash
pytest tests/ -v
```

Tests mock all external calls (LLM + DB) : run anywhere, no credentials needed.

---

## Project structure

```
eurospark/
├── src/eurospark/
│   ├── __init__.py
│   ├── config.py          # Pydantic v2 Settings
│   ├── db/
│   │   ├── client.py      # Supabase async client
│   │   └── seed.py        # One-time data seeder
│   └── agent/
│       ├── state.py       # GraphState TypedDict
│       ├── tools.py       # execute_sql + plot_chart tools
│       ├── nodes.py       # All 4 node functions
│       ├── prompts.py     # System prompts
│       └── graph.py       # StateGraph assembly + compile
├── frontend/
│   └── app.py             # Streamlit chat UI
├── tests/
│   ├── test_tools.py
│   └── test_graph.py
├── data/
│   ├── electricity_prices.csv
│   ├── consumption_by_sector.csv
│   └── renewable_capacity.csv
├── langgraph.json          # LangGraph Server config
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── Makefile
└── .env.example
```

---

## Why this project

Built as a portfolio demonstration of end-to-end LangGraph proficiency:
building a custom `StateGraph` from scratch (not using `create_react_agent`),
deploying it as a production API via LangGraph Server and connecting a
streaming frontend, all on free infrastructure.

Data domain chosen deliberately: EU electricity market data is directly
relevant to energy sector employers (Engie, TotalEnergies, RTE, Elia).
