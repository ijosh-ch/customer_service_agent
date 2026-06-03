# TODO

## Now

- [ ] Set `OPENAI_API_KEY=sk-...` in `.env` — required to run both notebooks
- [ ] Run `LLM project 1.ipynb` end-to-end with live output (all 11 test cases) to verify OpenAI integration
- [ ] Demo day prep: run `workspace-cli call list_calendars` (OAuth verify) before opening `LLM project 2.ipynb`

## Next

- [ ] Run `LLM project 2.ipynb` cells in order: prerequisites → OAuth verify → seed emails → seed calendar → Refund Agent AUTO → Calendar Agent DEMO
- [ ] Register MySQL as a Windows service if needed (Admin PowerShell):

  ```powershell
  icacls "D:\MySQL" /grant "NT AUTHORITY\SYSTEM:(OI)(CI)F" /T /Q
  icacls "D:\MySQL" /grant "BUILTIN\Administrators:(OI)(CI)F" /T /Q
  & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.4\my.ini" --install MySQL84
  Set-Service -Name MySQL84 -StartupType Automatic
  Start-Service -Name MySQL84
  ```

## Later

- [ ] Clean up `demo.ipynb` or consolidate into `LLM project 1.ipynb`
- [ ] Re-enable DGX Spark Nemotron (`nemotron.service`) if switching back from OpenAI
- [ ] Verify `workspace-cli call create_calendar_event` argument format — test the calendar pre-population cell before demo

## Completed

- [x] Apply ijosh-ch/claude preferences — `.claude/settings.json`, 4-file system, behavior/writing/git rules
- [x] Wire machine-level ijosh-ch/claude preferences — `~/.claude/prompts/` hook scripts, `~/.claude/settings.json` with UserPromptSubmit hook + bypassPermissions + effortLevel high
- [x] Create `.venv` with `--prompt llm` (shows `(llm)` in terminal), register `llms` Jupyter kernel
- [x] Verify MySQL DB connection to `140.118.122.119` — all 4 tables present
- [x] Create `LONG-TERM_MEMORY.md` documenting MySQL LTM setup
- [x] Draft `Project 2.ipynb` — all PDF sections covered (Project A + Project B)
- [x] Add Section 6.14 `_print_setup_guide()` to `Project 2.ipynb`
- [x] Replace brief GCP setup cell with click-by-click OAuth guide in `Project 2.ipynb`
- [x] Obtain Google Cloud OAuth credentials — Client ID + Secret in `.env`
- [x] Resolve merge conflict (`main.py` + `.env.example`) — took partner's 5-node architecture, fixed DB to 122.119 default
- [x] Rewrite `LLM project 1.ipynb` — 5-node architecture, all 11 tests auto-run
- [x] Create `LLM project 2.ipynb` — 63-cell authoritative demo notebook, all PDF gaps fixed
- [x] Fix 4 compliance gaps in `LLM project 2.ipynb`: model gpt-4o, Gmail scope, calendar prepop, duplicate function
- [x] Create `REQUIREMENTS.md` — from-scratch guide for both projects
- [x] Create `setup_db.py` — local MySQL init + seed script
- [x] Set up local MySQL on HDD (`D:\MySQL\data`) — `customer_service` DB, tables, seed data seeded
- [x] Switch both notebooks from DGX Spark Nemotron to OpenAI (Project 1: gpt-4o-mini, Project 2: gpt-4o)
- [x] Stop and disable `nemotron.service` on DGX Spark (140.118.122.123)
