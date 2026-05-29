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
