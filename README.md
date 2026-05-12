# Intelligent Customer Service Agent (ReAct + LangGraph)

This project implements a natural language-driven Customer Service Agent using the ReAct (Reason + Act) paradigm. Built with **LangGraph** and **gpt-4o-mini**, the agent dynamically interacts with a **MySQL** database to handle customer queries, process refunds, and log complaints while maintaining strict session memory and enforcing data access policies.

## Features
* **Multi-Step Reasoning:** Utilizes the ReAct framework to understand intents and generate execution plans.
* **Dynamic Tool Execution:** Connects directly to a MySQL database to look up orders, check customer profiles, process refunds, and log complaints.
* **Persistent Session Memory:** Maintains conversational context across turns using LangGraph's checkpointer.
* **Secure Data Access:** Enforces strict ID-based data ownership, preventing unauthorized access to other customers' data.
* **Verification Node:** Built-in compliance checking to prevent LLM hallucinations and enforce standard policies.

## Prerequisites

Before running this project, ensure you have the following installed:
1. **[uv](https://docs.astral.sh/uv/)**: An extremely fast Python package and project manager.
2. **MySQL Server**: Running locally or remotely.
3. **OpenAI API Key**: Required for the LangChain OpenAI integration.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name
```

### 2. Initialize the Database
The agent requires a specific database schema and mock data to function. 
1. Open your terminal or MySQL Workbench.
2. Run the provided SQL script to create the `customer_service` database and populate it with mock test cases:
```bash
mysql -u root -p < init_db.sql
```

### 3. Environment Configuration
This project uses environment variables to keep sensitive credentials secure.

1. Copy the example environment file to create your own local `.env` file:
   ```bash
   cp .env.example .env
   ```
2. Open the new `.env` file and fill in your actual credentials:
   ```env
   OPENAI_API_KEY=your-openai-api-key-here
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your-secure-password
   DB_NAME=customer_service
   ```

### 4. Install Dependencies
This project uses `uv` for incredibly fast dependency management. To install all required packages into an isolated virtual environment, run:
```bash
uv sync
```

## Running the Agent

With `uv`, you do not need to manually activate your virtual environment. You can execute the main script directly:

```bash
uv run main.py
```

### Example Interaction
When you run the script, the agent will load the session for a specific logged-in user (e.g., Customer ID 1) and process their query using its tools:

```text
User ID 1: whats my profile?

[Planner] Decided to call tools: ['customer_profile']
[Tool Execution] customer_profile: Customer profile found: {'customer_id': 1, 'name': 'Alice Smith', 'email': 'alice@example.com', ...}

[Final Response from Verifier]: Your profile name is Alice Smith, and your email is alice@example.com.
```

## Architecture Overview
* **Planner Node:** Extracts intent, identifies entities, and determines which tools to call based on the logged-in user's context.
* **Tool Nodes:** Executes secure, parameter-bound SQL queries against the MySQL database.
* **Verifier Node:** Reviews the final response to ensure policy compliance and data accuracy before outputting to the user.