# Long-Term Memory — MySQL Setup Guide

## Overview

This project follows the Claude long-term memory pattern: an external key-value store (MySQL) that persists customer preferences and history across sessions, scoped per user. The agent reads from it automatically when context is needed and writes to it when the user states a preference.

Claude's long-term memory guidelines recommend:

1. **Scoped storage** — memories belong to a specific user/entity, never shared across users.
2. **Key-value semantics** — each memory is a labelled fact (`key`, `value`), not a blob.
3. **Tool-mediated access** — the LLM calls explicit tools to read or write; it never accesses the DB directly.
4. **Explicit triggers** — the LLM writes to memory only when the user expresses a preference or important fact, not on every turn.

---

## Database Connection

| Parameter | Value |
| --- | --- |
| Host | `140.118.122.119` |
| Port | `3306` |
| Database | `llm-course` |
| User | `llm-student` |
| Password | `llm12345` |

Connection is established per-tool-call (open/close in `try/finally`) via `get_db_connection()` in `main.py`. Values are loaded from `.env` with the remote server as hard-coded fallback — the agent runs without a `.env` file as long as `OPENAI_API_KEY` is set.

---

## Table Schema

```sql
CREATE TABLE customer_memory (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    `key`       TEXT,
    value       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- `customer_id` — links memory to a specific customer (ownership enforcement)
- `key` — short label describing the fact (e.g. `resolution_preference`, `past_issues`)
- `value` — the fact itself, free-form text
- `created_at` — timestamp for ordering; `read_long_term_memory` returns rows sorted by `created_at DESC`

---

## Pre-Seeded Data

| id | customer_id | key | value |
| --- | --- | --- | --- |
| 1 | 1 | `resolution_preference` | `prefers refunds over store credit` |
| 2 | 3 | `past_issues` | `frequent late deliveries` |

These support Test 8 (LTM Read, Customer 3), Test 9 (LTM Write, Customer 1), and Test 10 (Personalization, Customer 3).

---

## LangGraph Tool Implementation

### Read (`read_long_term_memory`)

```python
@tool
def read_long_term_memory(config: RunnableConfig) -> str:
    """Read all long-term memory records (preferences, past issues) stored for this customer from MySQL."""
    customer_id = config["configurable"]["customer_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT `key`, value, created_at FROM customer_memory WHERE customer_id = %s ORDER BY created_at DESC;",
        (customer_id,),
    )
    results = cursor.fetchall()
    ...
```

### Write (`write_long_term_memory`)

```python
@tool
def write_long_term_memory(key: str, value: str, config: RunnableConfig) -> str:
    """Save a customer preference or important note to long-term memory in MySQL (persistent across sessions)."""
    customer_id = config["configurable"]["customer_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customer_memory (customer_id, `key`, value) VALUES (%s, %s, %s);",
        (customer_id, key, value),
    )
    conn.commit()
    ...
```

Both tools receive `config: RunnableConfig` as the last argument. LangGraph injects `customer_id` (and `thread_id`) from the graph's `configurable` dict at invocation time — no customer state is stored in tool arguments, preventing cross-customer data leakage.

---

## How Memory Is Triggered

The planner node's system prompt instructs the LLM when to use each tool:

| User Signal | Tool Invoked |
| --- | --- |
| "What issues have I had before?" | `read_long_term_memory` |
| "My order is late again" | `read_long_term_memory` (detects "again" as a personalization cue) |
| "Remember I prefer refunds" | `write_long_term_memory(key="resolution_preference", value=...)` |
| Any explicit preference statement | `write_long_term_memory` |

The LLM does not write on every turn — only when the user's message contains a clear preference or fact worth retaining.

---

## Re-Seeding the Database

If test data has been modified (e.g. after Test 9 writes a new LTM row), restore the original state:

```bash
mysql -h 140.118.122.119 -u llm-student -pllm12345 llm-course < init_db.sql
```

`init_db.sql` truncates all four tables and re-inserts the original seed rows.

---

## Verifying the Connection

```python
import mysql.connector
conn = mysql.connector.connect(
    host='140.118.122.119', port=3306,
    user='llm-student', password='llm12345',
    database='llm-course'
)
cur = conn.cursor()
cur.execute('SELECT * FROM customer_memory')
print(cur.fetchall())
cur.close(); conn.close()
```

Expected output (fresh DB):

```
[(1, 1, 'resolution_preference', 'prefers refunds over store credit', ...), 
 (2, 3, 'past_issues', 'frequent late deliveries', ...)]
```
