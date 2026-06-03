# TODO

## Now

- [ ] Set `OPENAI_API_KEY=sk-...` in `.env` — required to run both notebooks
- [ ] Run `LLM project 1.ipynb` end-to-end with live output (all 11 test cases) to verify OpenAI integration
- [ ] Run DB-reset cell before re-running Tests 4, 5, 6
- [ ] Register MySQL as a Windows service (run in **Admin PowerShell**):

  ```powershell
  icacls "D:\MySQL" /grant "NT AUTHORITY\SYSTEM:(OI)(CI)F" /T /Q
  icacls "D:\MySQL" /grant "BUILTIN\Administrators:(OI)(CI)F" /T /Q
  & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.4\my.ini" --install MySQL84
  Set-Service -Name MySQL84 -StartupType Automatic
  Start-Service -Name MySQL84
  ```

## Next

- [ ] Run `Project 2.ipynb` Credentials cell after setting `OPENAI_API_KEY`
- [ ] Run `Project 2.ipynb` Section 7 (Refund Email Agent) + Section 8 (Calendar Agent)
- [ ] Install `uv`, then `workspace-cli` (for Project 2):

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  git clone https://github.com/taylorwilsdon/google_workspace_mcp
  cd google_workspace_mcp && uv tool install . && pip install workspace-mcp
  ```

## Later

- [ ] Clean up `demo.ipynb` or consolidate into `LLM project 1.ipynb`
- [ ] Add interactive calendar example queries to `Project 2.ipynb` once credentials are working
- [ ] Re-enable DGX Spark Nemotron (`nemotron.service`) if switching back from OpenAI

## Completed

- [x] Apply ijosh-ch/claude preferences — `.claude/settings.json`, 4-file system, behavior/writing/git rules
- [x] Create `.venv` with `--prompt llm` (shows `(llm)` in terminal), register `llms` Jupyter kernel
- [x] Verify MySQL DB connection to `140.118.122.119` — all 4 tables present
- [x] Create `LONG-TERM_MEMORY.md` documenting MySQL LTM setup
- [x] Draft `Project 2.ipynb` — all 25 PDF sections covered (Project A + Project B)
- [x] Add Section 6.14 `_print_setup_guide()` to `Project 2.ipynb`
- [x] Replace brief GCP setup cell with 25-step click-by-click OAuth guide in `Project 2.ipynb`
- [x] Obtain Google Cloud OAuth credentials — Client ID + Secret in `.env`
- [x] Resolve merge conflict (`main.py` + `.env.example`) — took partner's 5-node architecture, fixed DB to 122.119 default
- [x] Rewrite `LLM project 1.ipynb` — 45 cells, 5-node architecture, all 11 tests auto-run
- [x] Create `REQUIREMENTS.md` — from-scratch guide for both projects
- [x] Create `setup_db.py` — local MySQL init + seed script
- [x] Set up local MySQL on HDD (`D:\MySQL\data`) — `customer_service` DB, tables, seed data seeded
- [x] Switch both notebooks from DGX Spark Nemotron to OpenAI gpt-4o-mini
- [x] Stop and disable `nemotron.service` on DGX Spark (140.118.122.123)
