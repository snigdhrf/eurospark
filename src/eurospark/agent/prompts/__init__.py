from .loader import load_md

# Pre-load all prompts into memory at startup
SUPERVISOR_PROMPT = load_md("supervisor_prompt")
SQL_AGENT_PROMPT = load_md("SQL_agent_prompt")
CHART_AGENT_PROMPT = load_md("chart_agent_prompt")
RESPONDER_PROMPT = load_md("responder_prompt")
CLARIFICATION_AGENT_PROMPT = load_md("clarification_agent_prompt")

# Export them so they are easy to import elsewhere
__all__ = [
    "SUPERVISOR_PROMPT",
    "SQL_AGENT_PROMPT",
    "CHART_AGENT_PROMPT",
    "RESPONDER_PROMPT",
    "CLARIFICATION_AGENT_PROMPT"
]