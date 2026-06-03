# CLAUDE.md — Intelligent Customer Service Agent

Static knowledge snapshot. Updated each session. Do not log prompting history here.

---

## Behavior

- **Do not auto-commit.** Always show the proposed commit message for review. The only exception is `git push`, which triggers the auto daily-log workflow and commits automatically.
- **Allow all commands** in this session unless explicitly restricted.
- Default to concise, direct responses — no trailing summaries.

## Writing Rules

- Do not use the § (section sign) symbol — write "Section" in full or omit the subsection reference.
- Do not use inline dashes (` - `) in prose — replace with a comma or rewrite the sentence.
- Default to writing no comments in code.
- No trailing summary at the end of responses — the user can read the diff.

## Git Workflow

- Never amend published commits — always create a new commit.
- Never skip hooks (`--no-verify`) unless explicitly requested.
- Stage specific files by name, never `git add -A` blindly.
- `git push` triggers the auto daily-log hook.
- **Commit style**: imperative title, `Work Start: hh:mm`, `Summary:` paragraph, `Details:` numbered list.

## Mandatory Project Files

Every session, read and maintain all four files:

| File | Purpose |
| --- | --- |
| `CLAUDE.md` | Static snapshot: rules, conventions, file list. Never log session activity here. |
| `CONTEXT.md` | Architecture overview, key files, external services. |
| `MEMORY.md` | Append-only session log. |
| `TODO.md` | Task list under Now / Next / Later. |

**Session START:** Read all four files. Run `git log -1 --format="%H %ai"` to mark session start.

**Session END:** Reconcile all four files, show commit message for review — do not run `git commit`.

---

## Project Overview

Natural language-driven Customer Service Agent built with **LangGraph** + **LangChain** + **OpenAI gpt-4o-mini**. Follows the **ReAct (Reason + Act)** paradigm: the LLM reasons about user intent, selects tools dynamically, executes MySQL queries, updates memory, and returns a verified response.

- **Course**: LLM Project 1
- **Deadline**: 2026-05-18 08:00 (Moodle submission); demo 2026-05-18–19 via Google Meet
- **Team size**: max 2 members
- **Language**: Python 3.10
- **Package manager**: uv

---

## File Inventory

| File | Purpose |
| --- | --- |
| `main.py` | Full agent: DB connection, 6 tools, 5-node LangGraph (memory_loader → planner ⇄ tools → verifier → memory_extractor), interactive CLI |
| `LLM project 1.ipynb` | Primary demo notebook — 45 cells, mirrors PDF sections 1–10, colleague's 5-node architecture, all 11 test cases run automatically; **primary demo notebook** |
| `demo.ipynb` | Supplementary demo notebook — all 11 test cases from Section 9, one cell per case; includes graph visualisation, DB-reset, and DB-verify cells |
| `LLMs-setup.ipynb` | DGX Spark vLLM server setup guide — installs vLLM, starts Nemotron 49B, opens network access; run on the DGX Spark (140.118.122.123) |
| `init_db.sql` | MySQL schema + seed data targeting remote `llm-course` DB; run with `mysql … < init_db.sql` |
| `setup_db.py` | Python script — creates DB + user (local admin flow), tables, and seed data; supports `--local`, `--from-env`, `--reset` flags |
| `REQUIREMENTS.md` | From-scratch setup guide for both projects — packages, MySQL (local + remote), uv, workspace-mcp, Google OAuth, env vars, verification |
| `Customer Service Agent.pdf` | Project 1 slide deck (from partner's main branch) |
| `pyproject.toml` | uv project config and Python dependencies |
| `uv.lock` | Locked dependency tree (committed, do not edit manually) |
| `.python-version` | Pins Python 3.10 for uv/pyenv |
| `.env.example` | Credentials template — `OPENAI_API_KEY` (primary), DGX Spark vars (optional), remote MySQL defaults, Google OAuth fields |
| `env_local_llm.yaml` | DGX Spark configuration reference — machine specs, vLLM server configs for Nemotron 49B and Llama 3.1 8B, Ollama models, launch commands, API key |
| `requirements.txt` | pip freeze snapshot of the current `.venv` — reference only, not used by uv |
| `.gitignore` | Excludes `.env`, `.venv`, `.claude/settings.local.json`, and `*.apps.googleusercontent.com.json` |
| `.vscode/settings.json` | VSCode workspace settings — pins Jupyter server to Python 3.12 (working `jupyter_server`) |
| `README.md` | Setup guide, architecture overview, example interaction |
| `LLM project 1.pdf` | Original project specification (Section 9 = grading checklist) |
| `CONTEXT.md` | Architecture snapshot |
| `MEMORY.md` | Append-only session log |
| `TODO.md` | Task list |
| `LONG-TERM_MEMORY.md` | MySQL LTM setup guide — schema, tools, seed data, re-seed instructions |
| `Project 2.ipynb` | AI Workspace Agent Suite — Refund Email Agent + Calendar Agent (Project 2) |
| `Project 2.pdf` | Project 2 specification |
| `AI Workspace Agent Suite.pdf` | Project 2 slide deck with architecture and setup details |

---

## Architecture

### LangGraph Workflow (5-node)

```text
User Input
    |
[memory_loader_node]  — loads all LTM from MySQL, injects as SystemMessage
    |
[planner_node]        — LLM reasons about intent, selects tools
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

Edge logic: `route_planner_output` → `"tools"` if the planner emitted tool calls, else `"verifier"`.

### Nodes

| Node | Function | File location |
| --- | --- | --- |
| `memory_loader_node` | Load all LTM at turn start, inject as SystemMessage | `main.py` |
| `planner_node` | Extract intent + entities, select tools | `main.py` |
| `ToolNode` (prebuilt) | Execute bound tool calls | `main.py` (LangGraph prebuilt) |
| `verifier_node` | Compliance check + rewrite if needed | `main.py` |
| `memory_extractor_node` | Auto-extract new preferences post-verifier, upsert to MySQL silently | `main.py` |

### Memory

| Type | Mechanism | Scope |
| --- | --- | --- |
| Short-term (STM) | `LangGraph` `MemorySaver` keyed on `thread_id` | Session (in-process) |
| Long-term (LTM) | MySQL `customer_memory` table on remote DB keyed on `customer_id` | Persistent across sessions |

---

## Tools (6 total)

All tools receive `config: RunnableConfig` injected by LangGraph. `customer_id` and `thread_id` are read from `config["configurable"]`.

| Tool | SQL Operation | Description |
| --- | --- | --- |
| `order_lookup(order_id)` | `SELECT * FROM orders WHERE order_id=? AND customer_id=?` | Retrieve order details |
| `customer_profile()` | `SELECT * FROM customers WHERE customer_id=?` | Retrieve customer profile |
| `request_refund(order_id)` | `UPDATE orders SET status='refund_requested' WHERE …` | Initiate refund |
| `log_complaint(order_id, issue)` | `INSERT INTO complaints (…)` | Log a complaint |
| `retrieve_memories()` | `SELECT key, value FROM customer_memory WHERE customer_id=?` | Read all LTM for this customer |
| `store_memory(key, value)` | `INSERT … ON DUPLICATE KEY UPDATE` (upsert) | Persist or update a preference |

All tools enforce **customer_id ownership** — queries are always scoped to the authenticated customer.

---

## Database

**Remote MySQL** (lab): `140.118.122.119:3306` / database `llm-course` / user `llm-student`

**Local MySQL** (this machine): `localhost:3306` / database `customer_service` / user `llm-student` / data on `D:\MySQL\data` (HDD). Config at `C:\ProgramData\MySQL\MySQL Server 8.4\my.ini`. Switch by editing `DB_HOST` and `DB_NAME` in `.env`.

```sql
customers      (customer_id PK, name, email, created_at)
orders         (order_id PK, customer_id, product_name, status, order_date, delivery_date)
complaints     (complaint_id PK AUTO, customer_id, order_id, issue, status, created_at)
customer_memory(id PK AUTO, customer_id, `key`, value, created_at)
```

### Mock Data (test-case aligned)

| customer_id | name | owns orders |
| --- | --- | --- |
| 1 | Alice Smith | 12345 (shipped), 5678 (delivered) |
| 2 | Bob Johnson | 1001 (processing), 7890 (delivered) |
| 3 | Charlie Davis | 2222 (delivered) |

Pre-seeded LTM:

- Customer 1: `resolution_preference = prefers refunds over store credit`
- Customer 3: `past_issues = frequent late deliveries`

---

## Test Score Checklist (Section 9)

| # | Function | Test Query | Customer | Expected |
| --- | --- | --- | --- | --- |
| 1 | Intent Parsing | Where is my order 12345? | 1 | intent=tracking, order_id extracted |
| 2 | OrderLookupTool | Check status of order 1001 | 2 | SELECT orders |
| 3 | CustomerProfileTool | Show my profile | 1 | SELECT customers |
| 4 | RefundTool | Refund order 5678 | 1 | UPDATE status=refund_requested |
| 5 | ComplaintLoggerTool | Complain about order 2222 | 3 | INSERT complaints |
| 6 | Multi-step Reasoning | Refund 7890 if delivered | 2 | lookup → conditional refund |
| 7 | STM | Cancel it (after order query) | 2 | recall order_id from same thread |
| 8 | LTM Read | What issues have I had before? | 3 | SELECT customer_memory |
| 9 | LTM Write | Remember I prefer refunds | 1 | INSERT customer_memory |
| 10 | Personalization | My order is late again | 3 | detect repeated issue from LTM |
| 11 | Verifier | Refund order 0000 | 1 | reject — order not found |

All 11 cases are individually runnable in `LLM project 1.ipynb`.

---

## Running

### Initial setup

```bash
# 1. (Optional) Re-seed the remote DB
mysql -h 140.118.122.119 -u llm-student -pllm12345 llm-course < init_db.sql

# 2. Configure credentials
cp .env.example .env
# Edit .env: set OPENAI_API_KEY (DB values already default to remote server)

# 3. Create and activate the virtual environment
python -m venv --prompt llm .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS/Linux

# 4. Install dependencies
pip install langchain langchain-openai langgraph langchain-mcp-adapters mysql-connector-python python-dotenv ipykernel jupyter nest-asyncio
python -m ipykernel install --user --name llms --display-name "llms"
```

### Run agent (CLI — interactive loop)

```bash
python main.py
# Prompts for customer_id, then accepts free-form queries until 'exit'
```

### Run demo notebook (primary)

```bash
# Open LLM project 1.ipynb — all 11 test cases with live output
jupyter notebook "LLM project 1.ipynb"
```

### Environment variables (`.env`)

```bash
OPENAI_API_KEY=...

DB_HOST=140.118.122.119
DB_PORT=3306
DB_USER=llm-student
DB_PASSWORD=llm12345
DB_NAME=llm-course

# Project 2 — Google Cloud OAuth 2.0
GOOGLE_OAUTH_CLIENT_ID=....apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-...
OAUTHLIB_INSECURE_TRANSPORT=1
```

`get_db_connection()` in `main.py` reads these with the remote values as hard-coded defaults, so the agent works even without a `.env` file as long as `OPENAI_API_KEY` is set.

---

## Conventions

- **Config injection**: tools accept `config: RunnableConfig` as the last argument; LangGraph injects `thread_id` and `customer_id` automatically.
- **Tool return type**: all tools return `str` (the LLM reads raw strings).
- **DB connections**: each tool opens/closes its own connection in a `try/finally` block.
- **Branch**: feature work on `jupyter`; stable on `main`.

---

## Working Sessions

2026/05/14: 12.00 - 12.25
2026/05/15: 17.15 - 18.15
2026/05/16: 00.58 - 02.28
2026/05/21: 14.00 - 18.15
2026/05/27: 11.00 – 12.20
2026/05/30: 02.20 – 02.43
2026/06/01: 23.00 – 24.00
2026/06/02: 00.00 – 00.31
2026/06/02: 08.00 – 12.30
2026/06/03: 11.30 – 12.39
