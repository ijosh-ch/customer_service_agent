# Context

## What This Project Is

Two-project suite for LLM courses at NTUST:

- **Project 1** — Intelligent Customer Service Agent built with LangGraph + LangChain + OpenAI gpt-4o-mini. Routes queries through a planner, optional tool calls, and a verifier.
- **Project 2** — AI Workspace Agent Suite: Refund Email Agent (Gmail MCP, 6-step autonomous workflow) + Calendar Agent (dual MCP/CLI tools, ReAct loop).

## Key Files

| Path | Role |
| --- | --- |
| `main.py` | Agent entry point: DB connection, 6 tools, 5-node LangGraph graph (memory_loader → planner ⇄ tools → verifier → memory_extractor), interactive CLI |
| `LLM project 1.ipynb` | Primary demo notebook — 45 cells, PDF sections 1–10, 5-node architecture, all 11 test cases auto-run |
| `Project 2.ipynb` | AI Workspace Agent Suite notebook — all PDF sections, both agents, 6.14 setup guide |
| `REQUIREMENTS.md` | Full from-scratch setup guide for both projects |
| `setup_db.py` | Local MySQL init script — creates DB, user, tables, seeds data |
| `demo.ipynb` | Supplementary notebook — one cell per test case, includes DB-reset and graph visualisation |
| `init_db.sql` | MySQL schema + seed data for remote `llm-course` DB |
| `LLMs-setup.ipynb` | vLLM server setup on the DGX Spark — reference only (Nemotron stopped) |
| `env_local_llm.yaml` | DGX Spark configuration reference — model specs, launch commands, API key |
| `pyproject.toml` | uv project config and dependency list |
| `.env.example` | Credentials template — `OPENAI_API_KEY`, DGX Spark vars (optional), DB defaults, Google OAuth fields |
| `LONG-TERM_MEMORY.md` | MySQL LTM schema, tools, seed data, and re-seed instructions |
| `CLAUDE.md` | Static rules, conventions, file inventory |
| `MEMORY.md` | Append-only session log |
| `TODO.md` | Task list |

## Architecture

```text
User Input
    |
[memory_loader_node]  — loads all LTM from MySQL, injects as SystemMessage
    |
[planner_node]        — gpt-4o-mini reasons about intent, selects tools
    |
    +-- tool_calls? --+
    |                 |
    |         [ToolNode]   — executes MySQL queries / business logic
    |                 |
    +<----------------+  (ReAct loop back to planner)
    |
[verifier_node]       — prevents hallucinations, enforces policy
    |
[memory_extractor_node] — auto-extracts new preferences, upserts to MySQL
    |
Final Response
```

Graph compilation: `route_planner_output` sends to `"tools"` if tool calls were emitted, otherwise to `"verifier"`.

## External Services

| Service | Address | Notes |
| --- | --- | --- |
| Remote MySQL (lab) | `140.118.122.119:3306` | DB `llm-course`, user `llm-student` |
| Local MySQL (this machine) | `localhost:3306` | DB `customer_service`, data on `D:\MySQL\data` (HDD); config at `C:\ProgramData\MySQL\MySQL Server 8.4\my.ini`; start: `mysqld.exe --defaults-file=...` |
| OpenAI API | `api.openai.com` | **Primary LLM** — both projects use `gpt-4o-mini`; key in `.env` as `OPENAI_API_KEY` |
| DGX Spark (lab) | `140.118.122.123` | NVIDIA GB10 Superchip; `nemotron.service` stopped and disabled — do not use Docker/vLLM until explicitly re-enabled |
| Google APIs | `gmail.googleapis.com`, `calendar.googleapis.com` | Project 2 — OAuth 2.0 Desktop App; client creds in `.env` |
| workspace-mcp | local subprocess via `uvx` | MCP server for Gmail + Calendar; tokens cached at `~/.workspace-mcp/` |

## Memory System

| Type | Mechanism | Scope |
| --- | --- | --- |
| Short-term (STM) | LangGraph `MemorySaver` keyed on `thread_id` | In-process session |
| Long-term (LTM) | MySQL `customer_memory` table keyed on `customer_id` | Persistent across sessions |

## Virtual Environment

`.venv` is created with `python -m venv --prompt llm .venv` — activating shows `(llm)` in the terminal prompt. Kernel registered as `llms` for Jupyter.
