# EuroSpark Graph Architecture

## Nodes

- **`supervisor`** — LLM with Pydantic structured output, no tools. Reads state and decides what to do next. Routes to worker nodes or responder. Always gets control back after each worker.

- **`schema_node`** — runs once at conversation start, fetches DB schema and caches it in state. No LLM needed, just a direct function call.

- **`sql_node`** — LLM generates the SQL query using schema from state, then directly calls `execute_sql`. Returns result to state.

- **`chart_node`** — LLM decides chart parameters, calls `plot_chart`. Returns base64 chart to state.

- **`error_node`** — triggered when a tool fails. LLM generates a helpful explanation of what went wrong and either triggers an interrupt (asks user to clarify) or flags for retry.

- **`responder`** — final LLM call, synthesizes everything in state into a natural language answer + chart. Always goes to `END`.

## Graph Sketch

```
START → schema_node → supervisor ←────────────────┐
                          │                        │
              ┌───────────┼───────────┐            │
              ↓           ↓           ↓            │
          sql_node   chart_node   error_node ──────┘
              └───────────┴───────────┘
                          │
                     supervisor
                          │
                     responder
                          │
                         END
```

## Key Decisions

- Supervisor uses Pydantic structured output with a `reasoning` field for debuggability
- Worker nodes each have their own focused LLM call + direct tool call
- `error_node` can trigger a human-in-the-loop interrupt
- LangGraph checkpointer handles conversation memory across turns
- Max iterations limit as a safety stop on the loop
