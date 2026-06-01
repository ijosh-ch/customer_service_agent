# Requirements — Building from Scratch

Covers both **Project 1** (Customer Service Agent) and **Project 2** (AI Workspace Agent Suite).

---

## System Requirements

| Requirement | Minimum | Recommended |
| --- | --- | --- |
| Python | 3.10 | 3.12+ |
| MySQL | 8.0 | 8.0+ |
| OS | Windows 10 / macOS 12 / Ubuntu 20.04 | Any |
| RAM | 4 GB | 8 GB |
| Internet | Required (OpenAI API + Google APIs) | — |

---

## Project 1 — Customer Service Agent

### Python Packages

```bash
pip install \
  langchain>=1.2 \
  langchain-openai>=1.2 \
  langchain-ollama>=1.1 \
  langgraph>=1.1 \
  mysql-connector-python>=9.7 \
  openai>=2.36 \
  python-dotenv>=1.2 \
  ipykernel \
  jupyter
```

Or if using `uv`:

```bash
uv sync          # installs from pyproject.toml
```

### API Keys

| Key | Where to get it | Required |
| --- | --- | --- |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) → API Keys | Yes |

### MySQL Database

Two options — **remote lab server** (no install needed) or **local MySQL**.

---

## MySQL Option A — Remote Lab Server (No Install)

The lab provides a shared MySQL server. Tables and seed data already exist.

| Parameter | Value |
| --- | --- |
| Host | `140.118.122.119` |
| Port | `3306` |
| Database | `llm-course` |
| User | `llm-student` |
| Password | `llm12345` |

The `.env` defaults are already set to this server — no further action needed.

To re-seed (if test data was modified):

```bash
mysql -h 140.118.122.119 -u llm-student -pllm12345 llm-course < init_db.sql
# or
python setup_db.py --from-env --reset
```

---

## MySQL Option B — Local MySQL

### Step 1 — Install MySQL

**Windows:**
1. Download MySQL Installer from [dev.mysql.com/downloads/installer](https://dev.mysql.com/downloads/installer)
2. Run the installer → choose **Server only** or **Developer Default**
3. During setup, set a **root password** — remember this
4. Start MySQL via **MySQL Workbench** or **Services**

Verify it's running:
```bash
mysql -u root -p
# should open a MySQL prompt
```

**macOS (Homebrew):**
```bash
brew install mysql
brew services start mysql
mysql_secure_installation   # set root password
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install mysql-server
sudo systemctl start mysql
sudo mysql_secure_installation
```

---

### Step 2 — Initialize the Database

Run the Python setup script. It creates the database, creates the `llm-student` user, creates all tables, and seeds all test data:

```bash
python setup_db.py --local --admin-password <your_root_password>
```

What it does:
- Creates database `customer_service`
- Creates user `llm-student@%` with password `llm12345`
- Grants full privileges on `customer_service`
- Creates all 4 tables
- Inserts all seed data (3 customers, 5 orders, 2 LTM rows)

To reset and re-seed later:
```bash
python setup_db.py --local --admin-password <root_password> --reset
```

Custom database or user:
```bash
python setup_db.py \
  --host localhost \
  --admin-user root \
  --admin-password secret \
  --db my_db \
  --user my_user \
  --password my_pass \
  --create-user
```

---

### Step 3 — Update `.env` for Local MySQL

```bash
# .env
OPENAI_API_KEY=sk-...

DB_HOST=localhost
DB_PORT=3306
DB_USER=llm-student
DB_PASSWORD=llm12345
DB_NAME=customer_service
```

The setup script prints the exact values at the end.

---

### Database Schema

```sql
customers (
    customer_id INT PRIMARY KEY,
    name        VARCHAR(100),
    email       VARCHAR(100),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

orders (
    order_id      INT PRIMARY KEY,
    customer_id   INT,
    product_name  TEXT,
    status        VARCHAR(50),         -- 'processing' | 'shipped' | 'delivered' | 'refund_requested'
    order_date    TIMESTAMP,
    delivery_date TIMESTAMP
)

complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id  INT,
    order_id     INT,
    issue        TEXT,
    status       VARCHAR(50),          -- 'open' | 'resolved'
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

customer_memory (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    `key`       TEXT,                  -- snake_case label, e.g. 'resolution_preference'
    value       TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Seed Data (Test-Case Aligned)

| Table | Row | Purpose |
| --- | --- | --- |
| customers | Alice Smith (id=1) | Tests 1, 3, 4, 9, 11 |
| customers | Bob Johnson (id=2) | Tests 2, 6, 7 |
| customers | Charlie Davis (id=3) | Tests 5, 8, 10 |
| orders | 12345, Alice, shipped | Test 1 — intent parsing |
| orders | 1001, Bob, processing | Tests 2, 7 — order lookup + STM |
| orders | 5678, Alice, delivered | Test 4 — refund |
| orders | 2222, Charlie, delivered | Test 5 — complaint |
| orders | 7890, Bob, delivered | Test 6 — multi-step refund |
| customer_memory | Charlie: past_issues | Tests 8, 10 — LTM read + personalization |
| customer_memory | Alice: resolution_preference | Test 9 baseline |

---

## Project 2 — AI Workspace Agent Suite

Project 2 requires everything from Project 1, plus the following.

### Additional Python Packages

```bash
pip install \
  langchain-mcp-adapters \
  nest_asyncio
```

### uv (Required for workspace-mcp)

`workspace-mcp` is launched via `uvx`, which is part of `uv`. Install `uv` first:

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Restart terminal after install
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal after install
```

Verify:
```bash
uv --version
uvx --version
```

### workspace-mcp + workspace-cli

```bash
git clone https://github.com/taylorwilsdon/google_workspace_mcp
cd google_workspace_mcp
uv tool install .       # installs workspace-cli globally
pip install workspace-mcp
```

Verify:
```bash
workspace-cli list      # should print available tools
```

### Google Cloud OAuth 2.0 Setup

#### Part 1 — Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top bar) → **New Project**
3. Name it `AI Workspace Agent` → **Create**

#### Part 2 — Enable APIs

4. Left sidebar: **APIs & Services** → **Library**
5. Search `Gmail API` → click it → **Enable**
6. Search `Google Calendar API` → click it → **Enable**

#### Part 3 — OAuth Consent Screen

7. Left sidebar: **APIs & Services** → **OAuth consent screen**
8. User Type: **External** → **Create**
9. Fill in:
   - App name: `AI Workspace Agent`
   - User support email: your email
   - Developer contact email: your email
10. **Save and Continue**
11. Click **Add or Remove Scopes** — add these 5:

    | Scope |
    | --- |
    | `https://mail.google.com/` |
    | `https://www.googleapis.com/auth/gmail.send` |
    | `https://www.googleapis.com/auth/gmail.modify` |
    | `https://www.googleapis.com/auth/calendar` |
    | `https://www.googleapis.com/auth/calendar.events` |

12. **Update** → **Save and Continue**
13. **Add Users** → add your Google account email → **Save and Continue**

#### Part 4 — Create OAuth Credentials

14. Left sidebar: **APIs & Services** → **Credentials**
15. **+ Create Credentials** → **OAuth client ID**
16. Application type: **Desktop app**
17. Name: `AI Workspace Agent Desktop` → **Create**
18. Copy the **Client ID** and **Client Secret** from the popup

#### Part 5 — Add to .env

```bash
GOOGLE_OAUTH_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxx
OAUTHLIB_INSECURE_TRANSPORT=1
```

#### Part 6 — First Run (Browser OAuth Consent)

When you run either agent for the first time, a browser window opens. Steps:
1. Sign in with the Google account you added in Part 3, Step 13
2. See the **"Google hasn't verified this app"** warning → click **Advanced** → **Go to AI Workspace Agent (unsafe)**
3. Approve all permissions → **Continue**
4. Browser shows **"The authentication flow has completed"** — close it
5. Tokens are cached at `~/.workspace-mcp/` (Fernet-encrypted). Not needed again unless you revoke access.

---

## Environment Variables Reference

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

| Variable | Required for | Description |
| --- | --- | --- |
| `OPENAI_API_KEY` | P1 + P2 | From [platform.openai.com](https://platform.openai.com) |
| `DB_HOST` | P1 + P2 | MySQL host — `140.118.122.119` (lab) or `localhost` |
| `DB_PORT` | P1 + P2 | MySQL port — `3306` |
| `DB_USER` | P1 + P2 | MySQL user — `llm-student` |
| `DB_PASSWORD` | P1 + P2 | MySQL password — `llm12345` |
| `DB_NAME` | P1 + P2 | Database name — `llm-course` (lab) or `customer_service` (local) |
| `GOOGLE_OAUTH_CLIENT_ID` | P2 only | From Google Cloud Console → OAuth 2.0 Client |
| `GOOGLE_OAUTH_CLIENT_SECRET` | P2 only | From Google Cloud Console → OAuth 2.0 Client |
| `OAUTHLIB_INSECURE_TRANSPORT` | P2 only | Set to `1` for local dev (skips HTTPS requirement) |

---

## Virtual Environment Setup

```bash
# Create venv — prompt shows (llm) in terminal when activated
python -m venv --prompt llm .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS / Linux)
source .venv/bin/activate

# Install all Project 1 dependencies
pip install langchain langchain-openai langchain-ollama langgraph \
            mysql-connector-python openai python-dotenv ipykernel jupyter

# Install additional Project 2 dependencies
pip install langchain-mcp-adapters nest_asyncio

# Register Jupyter kernel (so notebooks can find this venv)
python -m ipykernel install --user --name llms --display-name "llms"
```

---

## Quick Verification

After setup, run these checks to confirm everything is working:

### Check Python packages
```bash
python -c "import langchain, langgraph, mysql.connector, openai; print('All packages OK')"
```

### Check MySQL connection
```bash
python setup_db.py --from-env
# Should print: Connected + table row counts
```

Or for local:
```bash
python setup_db.py --local --admin-password <root_password>
```

### Check OpenAI API
```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model='gpt-4o-mini')
print(llm.invoke('say hello').content)
"
```

### Check workspace-cli (Project 2 only)
```bash
workspace-cli list
workspace-cli call list_calendars    # triggers OAuth on first call
```

### Run the agent (CLI)
```bash
python main.py
# Enter customer_id: 1
# You: Where is my order 12345?
```

### Run the demo notebook (Project 1)
```bash
jupyter notebook "LLM project 1.ipynb"
# Run all cells top-to-bottom — no user input required
```

### Run the demo notebook (Project 2)
```bash
jupyter notebook "Project 2.ipynb"
# Fill in the Credentials cell, then run all cells
```

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError: langchain` | Run `pip install langchain langchain-openai langgraph` |
| `mysql.connector.errors.DatabaseError: 1045 Access denied` | Wrong user/password — check `.env` |
| `mysql.connector.errors.InterfaceError: 2003 Can't connect` | MySQL not running, or wrong host/port |
| `openai.AuthenticationError` | `OPENAI_API_KEY` is missing or wrong in `.env` |
| `uvx: command not found` | `uv` is not installed — see uv install section above |
| `workspace-cli: command not found` | Did not run `uv tool install .` in the google_workspace_mcp folder |
| `redirect_uri_mismatch` (Google OAuth) | Credential type must be **Desktop app**, not Web application |
| `Access blocked: app not verified` | Click **Advanced** → **Go to ... (unsafe)** — expected for test apps |
| Test 4/6 fails (order not found for refund) | Run the DB reset cell in the notebook first |
| Test 7 (STM) "Cancel it" fails | Must run Test 2 first in the same session — same `thread_id` required |
