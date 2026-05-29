# Context

## What This Project Is

Two-project suite for LLM courses at NTUST:

- **Project 1** — Intelligent Customer Service Agent built with LangGraph + LangChain + OpenAI gpt-4o-mini. Routes queries through a planner, optional tool calls, and a verifier.
- **Project 2** — AI Workspace Agent Suite: Refund Email Agent (Gmail MCP, 6-step autonomous workflow) + Calendar Agent (dual MCP/CLI tools, ReAct loop).

## Key Files

| Path | Role |
| --- | --- |
| `main.py` | Agent entry point: DB connection, 6 tools, LangGraph graph, interactive CLI |
| `LLM project 1.ipynb` | Primary demo notebook — all 11 test cases with live output, mirrors PDF sections 1–10 |
| `demo.ipynb` | Supplementary notebook — one cell per test case, includes DB-reset and graph visualisation |
| `init_db.sql` | MySQL schema + seed data for remote `llm-course` DB |
| `pyproject.toml` | uv project config and dependency list |
| `.env.example` | Credentials template — DB defaults + Google OAuth fields |
| `Project 2.ipynb` | AI Workspace Agent Suite notebook — all PDF sections, both agents, 6.14 setup guide |
| `LONG-TERM_MEMORY.md` | MySQL LTM schema, tools, seed data, and re-seed instructions |
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
| OpenAI API | `api.openai.com` | Project 1: `gpt-4o-mini`; Project 2: `gpt-4o`; key from `.env` |
| Google APIs | `gmail.googleapis.com`, `calendar.googleapis.com` | Project 2 — OAuth 2.0 Desktop App; client creds in `.env` |
| workspace-mcp | local subprocess via `uvx` | MCP server for Gmail + Calendar; tokens cached at `~/.workspace-mcp/` |

## Memory System

| Type | Mechanism | Scope |
| --- | --- | --- |
| Short-term (STM) | LangGraph `MemorySaver` keyed on `thread_id` | In-process session |
| Long-term (LTM) | MySQL `customer_memory` table keyed on `customer_id` | Persistent across sessions |

## Virtual Environment

`.venv` is created with `python -m venv --prompt llm .venv` — activating shows `(llm)` in the terminal prompt. Kernel registered as `llms` for Jupyter.
