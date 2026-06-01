# Memory

Append-only session log. Add entries at session end; never delete or edit past entries.

---

## 2026/05/30

**Commit**: `0737a75` — 2026-05-27 12:19:26 +0800 (previous session boundary)

Completed Project 2 notebook and set up Google OAuth credentials:

- Cross-checked `AI Workspace Agent Suite.pdf` against `Project 2.ipynb` — found Section 6.14 `_print_setup_guide()` missing; added function and wired both `main()` orchestrators to call it on missing-env-var failure
- Replaced the brief 5-line GCP setup cell in `Project 2.ipynb` with a 25-step click-by-click guide (6 parts: create project, enable APIs, OAuth consent screen with all 5 required scopes, create Desktop App credentials, save to .env, first-run OAuth flow) plus a troubleshooting table for 4 common errors
- User downloaded `customer-agent.apps.googleusercontent.com.json` from Google Cloud Console — extracted `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` into `.env`
- Updated `.gitignore` with `*.apps.googleusercontent.com.json` pattern to prevent credential JSON commits
- Updated `.env.example` with Google OAuth field templates
- Key gotcha: OAuth credential type must be **Desktop app** — choosing Web application causes `redirect_uri_mismatch` error that is hard to diagnose

---

## 2026/06/02

**Commits**: `cb6de86`, `adc94b5` — 2026-06-01 23:13 and 23:30 +0800

Merged partner's improved architecture, rewrote the demo notebook, created from-scratch docs, and set up local MySQL on the HDD:

- Resolved merge conflict between `jupyter` and `main` branches: took partner's 5-node `main.py` (memory_loader_node, memory_extractor_node, store_memory/retrieve_memories with upsert logic) and fixed DB connection to use lab server 140.118.122.119 as default with localhost as a commented alternative
- Rewrote `LLM project 1.ipynb` — 45 cells using the colleague's 5-node architecture; mirrors PDF sections 1–10; DB reset cell + `run_test()` helper; all 11 test cases execute automatically with node-by-node trace output; Test 7 (STM) reuses Test 2's `thread_id`
- Created `REQUIREMENTS.md` — comprehensive from-scratch guide covering packages, MySQL (remote + local), uv, workspace-mcp, Google OAuth 6-part walkthrough, env vars, verification commands, troubleshooting
- Created `setup_db.py` — Python script with `--local`, `--from-env`, `--reset` flags; creates DB + user + tables + seed data; tested against remote lab server
- Set up local MySQL 8.4 on HDD: data at `D:\MySQL\data`, config at `C:\ProgramData\MySQL\MySQL Server 8.4\my.ini`; initialized with `--initialize`, started via direct `mysqld` process; created `customer_service` DB, `llm-student` user, all 4 tables, full seed data; `.env` updated to `localhost`
- Key gotcha: Windows service install (`mysqld --install`) requires admin AND the service account (SYSTEM) needs write permission to `D:\MySQL\data` via `icacls` — without this, service starts then immediately crashes with "ibdata1 must be writable"
- Partner uses `gpt-4o-mini` via `langchain_openai.ChatOpenAI`; `langchain-ollama` is listed as a dependency but never imported — was likely planned as a local fallback (Llama3, Mistral via Ollama)

---

## 2026-05-27

**Commit**: `325abf8` — 2026-05-21 22:38:21 +0800

Applied ijosh-ch/claude preferences to project:

- Created `.claude/settings.json` (bypassPermissions, additionalDirectories)
- Updated `CLAUDE.md` with behavior/writing/git rules and 4-file system; changed demo reference from `demo.ipynb` to `LLM project 1.ipynb`
- Created `CONTEXT.md`, `MEMORY.md`, `TODO.md`
- Updated `.gitignore` to exclude `.venv`
- Created `.venv` with `--prompt llm` (shows `(llm)` in terminal); installed all dependencies + ipykernel; registered `llms` kernel
- Verified DB connection to `140.118.122.119` — all 4 tables present, `customer_memory` has 2 seed rows
- Created `LONG-TERM_MEMORY.md` documenting MySQL LTM schema, tools, trigger conditions, and re-seed instructions
- Read all 3 PDFs (`LLM project 1.pdf`, `Project 2.pdf`, `AI Workspace Agent Suite.pdf`) via pypdf
- Verified `LLM project 1.ipynb` covers all 11 test cases — complete
- Drafted `Project 2.ipynb`: Project A (Refund Email Agent — Gmail MCP, 6-step workflow, 3 reply templates) + Project B (Calendar Agent — dual CLI/MCP tools, demo mode, interactive mode)
- Updated `TODO.md` with credential requirements for Project 2 activation
