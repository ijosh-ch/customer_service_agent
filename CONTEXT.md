# Context

## What This Project Is

Intelligent Customer Service Agent for LLM Project 1 (NTUST). Built with LangGraph + LangChain + OpenAI gpt-4o-mini, following the ReAct paradigm. The agent routes user queries through a planner, optional tool calls, and a verifier before responding.

## Key Files

| Path | Role |
| --- | --- |
| `main.py` | Agent entry point: DB connection, 6 tools, LangGraph graph, interactive CLI |
| `LLM project 1.ipynb` | Primary demo notebook — all 11 test cases with live output, mirrors PDF sections 1–10 |
| `demo.ipynb` | Supplementary notebook — one cell per test case, includes DB-reset and graph visualisation |
| `init_db.sql` | MySQL schema + seed data for remote `llm-course` DB |
| `pyproject.toml` | uv project config and dependency list |
| `.env.example` | Credentials template; DB defaults pre-filled for remote server |
| `CLAUDE.md` | Static rules, conventions, file inventory |
| `MEMORY.md` | Append-only session log |
| `TODO.md` | Task list |

## Architecture

```text
User Input
    |
[planner_node]    — gpt-4o-mini reasons about intent, selects tools
    |
    +-- tool_calls? --+
    |                 |
    |         [ToolNode]   — executes MySQL queries / business logic
    |                 |
    +<----------------+
    |
[verifier_node]   — prevents hallucinations, enforces policy
    |
Final Response
```

Graph compilation: `route_planner_output` sends to `"tools"` if tool calls were emitted, otherwise to `"verifier"`.

## External Services

| Service | Address | Notes |
| --- | --- | --- |
| Remote MySQL | `140.118.122.119:3306` | DB `llm-course`, user `llm-student` — no local MySQL needed |
| OpenAI API | `api.openai.com` | Model `gpt-4o-mini`, key from `.env` |

## Memory System

| Type | Mechanism | Scope |
| --- | --- | --- |
| Short-term (STM) | LangGraph `MemorySaver` keyed on `thread_id` | In-process session |
| Long-term (LTM) | MySQL `customer_memory` table keyed on `customer_id` | Persistent across sessions |

## Virtual Environment

`.venv` is created with `python -m venv --prompt llm .venv` — activating shows `(llm)` in the terminal prompt. Kernel registered as `llms` for Jupyter.
