import warnings
from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)

import os
import mysql.connector
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# LLM
# ==========================================
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ==========================================
# DATABASE CONNECTION (remote llm-course DB)
# ==========================================
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "140.118.122.119"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "llm-student"),
        password=os.getenv("DB_PASSWORD", "llm12345"),
        database=os.getenv("DB_NAME", "llm-course"),
    )

# ==========================================
# TOOLS
# ==========================================

@tool
def order_lookup(order_id: int, config: RunnableConfig) -> str:
    """Retrieve order details for a specific order ID."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM orders WHERE order_id = %s AND customer_id = %s;",
            (order_id, customer_id),
        )
        result = cursor.fetchone()
        return f"Order details: {result}" if result else f"No order found with ID {order_id} for this customer."
    except mysql.connector.Error as err:
        return f"Database error: {err}"
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


@tool
def customer_profile(config: RunnableConfig) -> str:
    """Retrieve the current customer's profile information."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM customers WHERE customer_id = %s;",
            (customer_id,),
        )
        result = cursor.fetchone()
        return f"Customer profile: {result}" if result else f"No customer found with ID {customer_id}."
    except mysql.connector.Error as err:
        return f"Database error: {err}"
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


@tool
def request_refund(order_id: int, config: RunnableConfig) -> str:
    """Initiate a refund for a specific order belonging to the current customer."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE orders SET status='refund_requested' WHERE order_id = %s AND customer_id = %s;",
            (order_id, customer_id),
        )
        conn.commit()
        if cursor.rowcount > 0:
            return f"Success: Order {order_id} has been updated to refund_requested."
        return f"Failed: Order {order_id} not found or does not belong to this customer."
    except mysql.connector.Error as err:
        return f"Database error: {err}"
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


@tool
def log_complaint(order_id: int, issue: str, config: RunnableConfig) -> str:
    """Log a customer complaint for a specific order."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO complaints (customer_id, order_id, issue, status) VALUES (%s, %s, %s, 'open');",
            (customer_id, order_id, issue),
        )
        conn.commit()
        return f"Success: Complaint logged for order {order_id}. Issue: {issue}"
    except mysql.connector.Error as err:
        return f"Database error: {err}"
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


@tool
def read_long_term_memory(config: RunnableConfig) -> str:
    """Read all long-term memory records (preferences, past issues) stored for this customer from MySQL."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT `key`, value, created_at FROM customer_memory WHERE customer_id = %s ORDER BY created_at DESC;",
            (customer_id,),
        )
        results = cursor.fetchall()
        if results:
            lines = [f"- {r['key']}: {r['value']} (saved: {r['created_at']})" for r in results]
            return f"Long-term memory for customer {customer_id}:\n" + "\n".join(lines)
        return f"No long-term memory found for customer {customer_id}."
    except mysql.connector.Error as err:
        return f"Database error: {err}"
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


@tool
def write_long_term_memory(key: str, value: str, config: RunnableConfig) -> str:
    """Save a customer preference or important note to long-term memory in MySQL (persistent across sessions)."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customer_memory (customer_id, `key`, value) VALUES (%s, %s, %s);",
            (customer_id, key, value),
        )
        conn.commit()
        return f"Saved to long-term memory: '{key}' = '{value}' for customer {customer_id}."
    except mysql.connector.Error as err:
        return f"Database error: {err}"
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


# Bind all tools to the LLM
tools = [
    order_lookup,
    customer_profile,
    request_refund,
    log_complaint,
    read_long_term_memory,
    write_long_term_memory,
]
llm_with_tools = llm.bind_tools(tools)

# ==========================================
# STATE
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# ==========================================
# NODES
# ==========================================

def planner_node(state: AgentState):
    """ReAct Planner: extracts intent + entities, selects tools."""
    system_prompt = SystemMessage(
        content=(
            "You are an intelligent customer service agent following the ReAct paradigm.\n"
            "Step 1 — Reason: analyze the user's input, identify intent (tracking, refund, complaint, "
            "memory query, preference), and extract entities (order_id, product).\n"
            "Step 2 — Act: select the appropriate tool(s).\n\n"
            "Available tools: order_lookup, customer_profile, request_refund, log_complaint, "
            "read_long_term_memory, write_long_term_memory.\n\n"
            "Guidelines:\n"
            "- Multi-step (e.g. 'refund if delivered'): call order_lookup first, then decide.\n"
            "- Personalization (e.g. 'late again'): call read_long_term_memory first.\n"
            "- Preference storage: call write_long_term_memory.\n"
            "- Always scope queries to the authenticated customer."
        )
    )
    response = llm_with_tools.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}


def verifier_node(state: AgentState):
    """Verifier: prevents hallucinations and enforces policy compliance."""
    verify_prompt = SystemMessage(
        content=(
            "You are a strict compliance verifier for a customer service agent.\n"
            "Review the conversation and the proposed response.\n"
            "Rules:\n"
            "1. Do NOT hallucinate order details, customer data, or outcomes.\n"
            "2. If a tool returned 'not found', the response must acknowledge this — never invent data.\n"
            "3. Be polite, empathetic, and professional.\n"
            "4. If the proposed response violates policy or contains hallucinations, rewrite it safely.\n"
            "Output only the final customer-facing response."
        )
    )
    verified_response = llm.invoke([verify_prompt] + state["messages"])
    return {"messages": [verified_response]}

# ==========================================
# EDGE LOGIC
# ==========================================

def route_planner_output(state: AgentState) -> Literal["tools", "verifier"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "verifier"

# ==========================================
# GRAPH
# ==========================================

workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("verifier", verifier_node)

workflow.add_edge(START, "planner")
workflow.add_conditional_edges("planner", route_planner_output)
workflow.add_edge("tools", "verifier")
workflow.add_edge("verifier", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# ==========================================
# CLI ENTRY POINT
# ==========================================

if __name__ == "__main__":
    import uuid

    print("=" * 60)
    print("  Intelligent Customer Service Agent (ReAct + LangGraph)")
    print("  LTM backend : MySQL @ 140.118.122.119 / llm-course")
    print("  STM backend : LangGraph MemorySaver (in-process)")
    print("=" * 60)

    customer_id = int(input("\nEnter customer_id (1=Alice, 2=Bob, 3=Charlie): ").strip() or "1")
    thread_id = f"cli_{uuid.uuid4().hex[:8]}"
    print(f"\nSession started. Thread: {thread_id}  Customer: {customer_id}")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break
        if not user_input:
            continue

        cfg = {"configurable": {"thread_id": thread_id, "customer_id": customer_id}}
        events = app.stream(
            {"messages": [HumanMessage(content=user_input)]},
            cfg,
            stream_mode="values",
        )

        for event in events:
            msg = event["messages"][-1]
            if isinstance(msg, AIMessage) and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"  [Planner → Tool] {tc['name']}({tc.get('args', {})})")
            elif msg.type == "tool":
                preview = msg.content[:200] + ("..." if len(msg.content) > 200 else "")
                print(f"  [Tool Result]    {preview}")
            elif isinstance(msg, AIMessage) and not msg.tool_calls:
                print(f"\nAgent: {msg.content}\n")
