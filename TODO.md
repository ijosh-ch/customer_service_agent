# TODO

## Now

- [ ] Provide Google Workspace credentials to activate Project 2.ipynb agents:
  - `GOOGLE_OAUTH_CLIENT_ID` — from Google Cloud Console OAuth 2.0 Desktop App
  - `GOOGLE_OAUTH_CLIENT_SECRET` — from Google Cloud Console OAuth 2.0 Desktop App
  - `OAUTHLIB_INSECURE_TRANSPORT=1` — for local dev
- [ ] Install `workspace-cli`:

  ```bash
  git clone https://github.com/taylorwilsdon/google_workspace_mcp
  cd google_workspace_mcp && uv tool install .
  pip install workspace-mcp
  ```

- [ ] Verify `LLM project 1.ipynb` runs all 11 test cases end-to-end with live output

## Next

- [ ] Run Project 2.ipynb Credentials cell after obtaining Google OAuth credentials
- [ ] Run DB-reset cell in `LLM project 1.ipynb` before re-running Tests 4, 5, 6
- [ ] Confirm `llms` kernel is visible in Jupyter when opening both notebooks
- [ ] Add `ipykernel`, `jupyter`, `langchain-mcp-adapters`, `nest_asyncio` as explicit deps in `pyproject.toml`

## Later

- [ ] Explore migrating from Python 3.13 venv to uv-managed Python 3.10 venv once uv is installed
- [ ] Clean up `demo.ipynb` or consolidate into `LLM project 1.ipynb`
- [ ] Add interactive calendar example queries to Project 2.ipynb once credentials are working
