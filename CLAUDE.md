# CLAUDE.md — Intelligent Customer Service Agent

Static knowledge snapshot. Updated each session. Do not log prompting history here.

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
| `main.py` | Full agent: DB connection, all 6 tools, LangGraph nodes, graph compilation, interactive CLI entry point |
| `demo.ipynb` | Jupyter demo notebook — all 11 test cases from Section 9, one cell per case, with DB-verify cell for Test 9 |
| `init_db.sql` | MySQL schema + seed data targeting remote `llm-course` DB; run with `mysql … < init_db.sql` |
| `pyproject.toml` | uv project config and Python dependencies |
| `uv.lock` | Locked dependency tree (committed, do not edit manually) |
| `.python-version` | Pins Python 3.10 for uv/pyenv |
| `.env.example` | Template for required environment variables (DB defaults pre-filled for remote server) |
| `.gitignore` | Excludes `.env` |
| `README.md` | Setup guide, architecture overview, example interaction |
| `LLM project 1.pdf` | Original project specification (Section 9 = grading checklist) |

---

## Architecture

### LangGraph Workflow

```text
User Input
    |
[Planner Node]   — LLM reasons about intent, selects tools
    |
    +-- tool_calls? --+
    |                 |
    |         [Tool Node(s)]   — executes MySQL queries / business logic
    |                 |
    +<----------------+
    |
[Verifier Node]  — prevents hallucinations, enforces policy
    |
Final Response
```

Edge logic: `route_planner_output` → `"tools"` if the planner emitted tool calls, else `"verifier"`.

### Nodes

| Node | Function | File location |
| --- | --- | --- |
| `planner_node` | Extract intent + entities, select tools | `main.py` |
| `ToolNode` (prebuilt) | Execute bound tool calls | `main.py` (LangGraph prebuilt) |
| `verifier_node` | Compliance check + rewrite if needed | `main.py` |

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
| `read_long_term_memory()` | `SELECT key, value FROM customer_memory WHERE customer_id=?` | Read LTM preferences/history |
| `write_long_term_memory(key, value)` | `INSERT INTO customer_memory (…)` | Persist a preference or note |

All tools enforce **customer_id ownership** — queries are always scoped to the authenticated customer.

---

## Database

**Remote MySQL**: `140.118.122.119:3306` / database `llm-course` / user `llm-student`

All four tables live on this server; no local MySQL is required.

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

All 11 cases are individually runnable in `demo.ipynb`.

---

## Running

### Initial setup

```bash
# 1. (Optional) Re-seed the remote DB
mysql -h 140.118.122.119 -u llm-student -pllm12345 llm-course < init_db.sql

# 2. Configure credentials
cp .env.example .env
# Edit .env: set OPENAI_API_KEY (DB values already default to remote server)

# 3. Install dependencies
uv sync
```

### Run agent (CLI — interactive loop)

```bash
uv run main.py
# Prompts for customer_id, then accepts free-form queries until 'exit'
```

### Run demo (Jupyter)

```bash
uv run jupyter notebook demo.ipynb
# or
uv run jupyter lab
```

### Environment variables (`.env`)

```bash
OPENAI_API_KEY=...

DB_HOST=140.118.122.119
DB_PORT=3306
DB_USER=llm-student
DB_PASSWORD=llm12345
DB_NAME=llm-course
```

`get_db_connection()` in `main.py` reads these with the remote values as hard-coded defaults, so the agent works even without a `.env` file as long as `OPENAI_API_KEY` is set.

---

## Conventions

- **Config injection**: tools accept `config: RunnableConfig` as the last argument; LangGraph injects `thread_id` and `customer_id` automatically.
- **Tool return type**: all tools return `str` (the LLM reads raw strings).
- **DB connections**: each tool opens/closes its own connection in a `try/finally` block.
- **Commit style**: imperative title, `Work Start: hh:mm`, `Summary:` paragraph, `Details:` numbered list.
- **Branch**: feature work on `jupyter`; stable on `main`.

---

## Working Sessions

2026/05/14: 12.00 - 12.25
2026/05/15: 17.15 - 18.15
