# TODO

## Now

- [ ] Fill in `OPENAI_API_KEY` in `.env` (only remaining blank credential)
- [ ] Install `uv`, then `workspace-cli`:

  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  # restart terminal, then:
  git clone https://github.com/taylorwilsdon/google_workspace_mcp
  cd google_workspace_mcp
  uv tool install .
  pip install workspace-mcp
  ```

- [ ] Run the **Credentials cell** in `Project 2.ipynb` to verify all 3 keys load correctly

## Next

- [ ] Run `Project 2.ipynb` Section 7 (Refund Email Agent auto mode) with live OAuth flow
- [ ] Run `Project 2.ipynb` Section 8 (Calendar Agent demo mode — 3 pre-written queries)
- [ ] Verify `LLM project 1.ipynb` runs all 11 test cases end-to-end with live output
- [ ] Run DB-reset cell in `LLM project 1.ipynb` before re-running Tests 4, 5, 6
- [ ] Confirm `llms` kernel is visible in Jupyter when opening both notebooks
- [ ] Add `ipykernel`, `jupyter`, `langchain-mcp-adapters`, `nest_asyncio` as explicit deps in `pyproject.toml`

## Later

- [ ] Explore migrating from Python 3.13 venv to uv-managed Python 3.10 venv once uv is installed
- [ ] Clean up `demo.ipynb` or consolidate into `LLM project 1.ipynb`
- [ ] Add interactive calendar example queries to `Project 2.ipynb` once credentials are working

## Completed

- [x] Apply ijosh-ch/claude preferences — `.claude/settings.json`, 4-file system, behavior/writing/git rules
- [x] Create `.venv` with `--prompt llm` (shows `(llm)` in terminal), register `llms` Jupyter kernel
- [x] Verify MySQL DB connection to `140.118.122.119` — all 4 tables present
- [x] Create `LONG-TERM_MEMORY.md` documenting MySQL LTM setup
- [x] Draft `Project 2.ipynb` — all 25 PDF sections covered (Project A + Project B)
- [x] Add Section 6.14 `_print_setup_guide()` to `Project 2.ipynb`
- [x] Replace brief GCP setup cell with 25-step click-by-click OAuth guide in `Project 2.ipynb`
- [x] Obtain Google Cloud OAuth credentials — Client ID + Secret in `.env`
- [x] Update `.gitignore` with `*.apps.googleusercontent.com.json` pattern
