import warnings
from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
warnings.filterwarnings(
    "ignore",
    category=LangChainPendingDeprecationWarning
)
import os
import json
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
# Set your OpenAI API Key
from dotenv import load_dotenv
load_dotenv()
config = {
    'customer_id': 1, 
    }
# Initialize your chosen LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# ==========================================
# 1. DATABASE CONNECTION (Mocked for safety)
# ==========================================
def get_db_connection():
    # Replace with your actual MySQL credentials
    # return mysql.connector.connect(
    #         host="localhost",
    #         user="root",
    #         password="12345678", 
    #         database="customer_service", 
    #     )
    return mysql.connector.connect(
            host=os.getenv("DATABASE_URL", "localhost"),
            user=os.getenv("DATABASE_USER", "root"),
            password=os.getenv("DATABASE_PASSWORD", "12345678"), 
            database=os.getenv("DATABASE_NAME", "customer_service"),
    )
# ==========================================
# 2. DEFINE TOOLS
# ==========================================
@tool
def order_lookup(order_id: int, config: RunnableConfig) -> str:
    """Retrieve order details for a specific order ID."""
    verify_customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) 
        
        query = "SELECT * FROM orders WHERE order_id = %s AND customer_id = %s;"
        cursor.execute(query, (order_id, verify_customer_id))
        result = cursor.fetchone()
        
        if result:
            return f"Order details found: {result}"
        else:
            return f"No order found with ID {order_id}."
            
    except mysql.connector.Error as err:
        return f"Database error occurred: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
@tool
def customer_profile(config: RunnableConfig) -> str:
    """Retrieve customer profile information."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM customers WHERE customer_id = %s;"
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()
        
        if result:
            return f"Customer profile found: {result}"
        else:
            return f"No customer found with ID {customer_id}."
            
    except mysql.connector.Error as err:
        return f"Database error occurred: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
@tool
def request_refund(order_id: int, config: RunnableConfig) -> str:
    """Initiate a refund for a specific order."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "UPDATE orders SET status='refund_requested' WHERE order_id = %s AND customer_id = %s;"
        cursor.execute(query, (order_id, customer_id))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return f"Success: Order {order_id} status updated to refund_requested."
        else:
            return f"Failed: No order found with ID {order_id} to update."
            
    except mysql.connector.Error as err:
        return f"Database error occurred: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
@tool
def log_complaint(order_id: int, issue: str, config: RunnableConfig) -> str:
    """Log a customer complaint."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "INSERT INTO complaints (customer_id, order_id, issue, status) VALUES (%s, %s, %s, 'open');"
        cursor.execute(query, (customer_id, order_id, issue))
        
        conn.commit()
        
        return f"Success: Complaint logged for order {order_id}."
        
    except mysql.connector.Error as err:
        return f"Database error occurred: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
# ==========================================
# 2b. LONG-TERM MEMORY TOOLS
# ==========================================
@tool
def store_memory(key: str, value: str, config: RunnableConfig) -> str:
    """Store a piece of long-term memory about the customer (e.g. preferences, 
    communication style, important facts). The key should be a short descriptive 
    label like 'preferred_language', 'tone_preference', 'product_interest'. 
    The value is the detail to remember."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Upsert: if a memory with the same key exists for this customer, update it.
        # Otherwise insert a new row. This prevents duplicate keys piling up.
        # First check if it exists
        cursor.execute(
            "SELECT id FROM customer_memory WHERE customer_id = %s AND `key` = %s;",
            (customer_id, key)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "UPDATE customer_memory SET `value` = %s, created_at = CURRENT_TIMESTAMP "
                "WHERE customer_id = %s AND `key` = %s;",
                (value, customer_id, key)
            )
        else:
            cursor.execute(
                "INSERT INTO customer_memory (customer_id, `key`, `value`) VALUES (%s, %s, %s);",
                (customer_id, key, value)
            )
        conn.commit()
        return f"Memory stored: {key} = {value}"
    except mysql.connector.Error as err:
        return f"Database error occurred: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
@tool
def retrieve_memories(config: RunnableConfig) -> str:
    """Retrieve all stored long-term memories/preferences for the current customer."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT `key`, `value`, created_at FROM customer_memory "
            "WHERE customer_id = %s ORDER BY created_at DESC;",
            (customer_id,)
        )
        results = cursor.fetchall()
        if results:
            # Convert datetime objects to strings for clean serialization
            for r in results:
                if r.get("created_at"):
                    r["created_at"] = str(r["created_at"])
            return f"Customer memories: {results}"
        else:
            return "No stored memories found for this customer."
    except mysql.connector.Error as err:
        return f"Database error occurred: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
# Bind ALL tools (including memory tools) to the LLM
tools = [order_lookup, customer_profile, request_refund, log_complaint, store_memory, retrieve_memories]
llm_with_tools = llm.bind_tools(tools)
# ==========================================
# 3. DEFINE THE STATE
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
# ==========================================
# 4. DEFINE THE NODES
# ==========================================
def memory_loader_node(state: AgentState, config: RunnableConfig):
    """
    Runs at the START of every turn. Loads all long-term memories from MySQL
    and injects them as a system message so the planner has full context about
    the customer's known preferences and history.
    """
    customer_id = config["configurable"]["customer_id"]
    memories_text = "No previous memories stored for this customer."
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT `key`, `value` FROM customer_memory WHERE customer_id = %s ORDER BY created_at DESC;",
            (customer_id,)
        )
        results = cursor.fetchall()
        if results:
            formatted = "\n".join([f"- {r['key']}: {r['value']}" for r in results])
            memories_text = f"Known customer preferences and facts:\n{formatted}"
    except mysql.connector.Error as err:
        memories_text = f"(Could not load memories: {err})"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
    memory_message = SystemMessage(
        content=f"[Long-Term Memory Context]\n{memories_text}\n\n"
                "Use this information to personalize your responses. "
                "For example, if the customer prefers formal language, respond formally."
    )
    return {"messages": [memory_message]}
def planner_node(state: AgentState):
    """
    Extracts intent, extracts entities, and generates an execution plan.
    """
    system_prompt = SystemMessage(
        content="You are an intelligent customer service agent. "
                "Analyze the user's input, extract intents (refund, tracking, complaint), "
                "and extract entities (order id). Select the appropriate tools to fulfill the request. "
                "You also have access to long-term memory tools: use 'store_memory' to save "
                "important customer preferences or facts you learn during the conversation, "
                "and 'retrieve_memories' to look up what you already know about them."
    )
    response = llm_with_tools.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}
def verifier_node(state: AgentState):
    """
    Ensures correctness, prevents hallucinations, and enforces policy compliance.
    """
    verify_prompt = SystemMessage(
        content="You are a strict compliance verifier for a customer service agent. "
                "Review the proposed response. Ensure it does not hallucinate data, "
                "is polite, and complies with standard refund/complaint policies. "
                "If it is good, output the exact response. If it violates policy, rewrite it safely."
    )
    verified_response = llm.invoke([verify_prompt] + state["messages"])
    return {"messages": [verified_response]}
def memory_extractor_node(state: AgentState, config: RunnableConfig):
    """
    Runs AFTER the verifier. Analyzes the full conversation to extract any new 
    preferences or facts about the customer that should be remembered long-term.
    Stores them directly into MySQL (not via tool calls, to keep the graph simple).
    """
    customer_id = config["configurable"]["customer_id"]
    # Build a focused extraction prompt
    extraction_prompt = SystemMessage(
        content=(
            "You are a memory extraction module. Analyze the conversation below and extract "
            "any NEW customer preferences, habits, or important facts worth remembering for "
            "future interactions. Examples:\n"
            "- Communication preferences (formal/informal tone, language)\n"
            "- Product preferences (favorite categories, sizes, colors)\n"
            "- Contact preferences (preferred contact method, best time to reach)\n"
            "- Recurring issues or sensitivities\n"
            "- Stated likes/dislikes\n"
            "- Service preferences (e.g., customer prefers refunds to be cancellable)\n\n"
            "Return a JSON array of objects with 'key' and 'value' fields. "
            "Use short, descriptive snake_case keys. "
            "If there is nothing new to remember, return an empty array: []\n\n"
            "IMPORTANT: Only extract genuinely useful long-term facts. Do NOT extract:\n"
            "- One-time transactional details (order IDs, refund statuses)\n"
            "- Information that is already stored in the memory context\n"
            "- Vague or speculative inferences\n\n"
        )
    )
    # Only send the human and AI messages (skip system/tool messages to reduce noise)
    conversation_messages = [
        msg for msg in state["messages"]
        if isinstance(msg, (HumanMessage, AIMessage)) and not getattr(msg, 'tool_calls', None)
    ]
    response = llm.invoke([extraction_prompt] + conversation_messages)
    # Parse the LLM's JSON output and store each memory
    try:
        # Strip markdown code fences if present
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]  # remove first line (```json)
            content = content.rsplit("```", 1)[0]  # remove trailing ```
            content = content.strip()
        memories = json.loads(content)
        if memories and isinstance(memories, list):
            conn = get_db_connection()
            cursor = conn.cursor()
            for mem in memories:
                key = mem.get("key", "").strip()
                value = mem.get("value", "").strip()
                if not key or not value:
                    continue
                # Upsert logic: update if exists, insert if new
                cursor.execute(
                    "SELECT id FROM customer_memory WHERE customer_id = %s AND `key` = %s;",
                    (customer_id, key)
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute(
                        "UPDATE customer_memory SET `value` = %s, created_at = CURRENT_TIMESTAMP "
                        "WHERE customer_id = %s AND `key` = %s;",
                        (value, customer_id, key)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO customer_memory (customer_id, `key`, `value`) VALUES (%s, %s, %s);",
                        (customer_id, key, value)
                    )
            conn.commit()
            cursor.close()
            conn.close()
    except (json.JSONDecodeError, Exception):
        # If extraction fails, silently continue — memory is best-effort
        pass
    # This node doesn't add messages to the conversation (invisible to the user)
    return {"messages": []}
# ==========================================
# 5. EDGE LOGIC
# ==========================================
def route_planner_output(state: AgentState) -> Literal["tools", "verifier"]:
    """
    Conditional edge: If the planner decided to call a tool, go to Tool Node. 
    Otherwise, go straight to the Verifier.
    """
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "verifier"
# ==========================================
# 6. BUILD THE GRAPH
# ==========================================
#
# Flow:
#   START -> memory_loader -> planner -> [tools | verifier]
#                                          |         |
#                                          v         |
#                                       planner <----+  (tools loop back to planner for ReAct)
#                                          |
#                                          v
#                                       verifier -> memory_extractor -> END
#
workflow = StateGraph(AgentState)
# Add Nodes
workflow.add_node("memory_loader", memory_loader_node)
workflow.add_node("planner", planner_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("verifier", verifier_node)
workflow.add_node("memory_extractor", memory_extractor_node)
# Add Edges
workflow.add_edge(START, "memory_loader")
workflow.add_edge("memory_loader", "planner")
workflow.add_conditional_edges("planner", route_planner_output)
workflow.add_edge("tools", "planner")  # ReAct loop: tool results go back to planner
workflow.add_edge("verifier", "memory_extractor")
workflow.add_edge("memory_extractor", END)
# Compile with Short-Term Memory Checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
# ==========================================
# 7. RUN THE AGENT (Example Test)
# ==========================================
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "customer_session_001", "customer_id": 2}}
    
    # # --- Turn 1: User reveals a preference ---
    # user_query = "Hi, I always prefer email for communication. Can you check my order 1001?"
    # print(f"User: {user_query}\n")
    
    # events = app.stream(
    #     {"messages": [HumanMessage(content=user_query)]}, 
    #     config, 
    #     stream_mode="values"
    # )
    
    # for event in events:
    #     message = event["messages"][-1]
    #     if isinstance(message, AIMessage) and message.tool_calls:
    #         print(f"[Planner] Decided to call tools: {[t['name'] for t in message.tool_calls]}")
    #     elif message.type == "tool":
    #         print(f"[Tool Execution] {message.name}: {message.content}")
    #     elif isinstance(message, AIMessage) and not message.tool_calls:
    #          print(f"\n[Final Response from Verifier]: {message.content}")
    # # --- Turn 2: The agent should already know the preference ---
    # print("\n" + "="*60 + "\n")
    # user_query_2 = "I want a refund for order 1001"
    # print(f"User: {user_query_2}\n")
    
    # events = app.stream(
    #     {"messages": [HumanMessage(content=user_query_2)]}, 
    #     config, 
    #     stream_mode="values"
    # )
    
    # for event in events:
    #     message = event["messages"][-1]
    #     if isinstance(message, AIMessage) and message.tool_calls:
    #         print(f"[Planner] Decided to call tools: {[t['name'] for t in message.tool_calls]}")
    #     elif message.type == "tool":
    #         print(f"[Tool Execution] {message.name}: {message.content}")
    #     elif isinstance(message, AIMessage) and not message.tool_calls:
    #          print(f"\n[Final Response from Verifier]: {message.content}")

    print("=" * 60)
    print("  Customer Service Agent (type 'quit' or 'exit' to stop)")
    print("=" * 60)
    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break
        events = app.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config,
            stream_mode="updates"
        )
        # seen_ids = set()
        for event in events:
             # event is a dict like {"planner": {"messages": [...]}}
            for node_name, state_update in event.items():
                messages = state_update.get("messages", [])
                for message in messages:
                    if node_name == "planner" and isinstance(message, AIMessage) and message.tool_calls:
                        print(f"[Planner] Calling tools: {[t['name'] for t in message.tool_calls]}")
                    elif node_name == "tools":
                        print(f"[Tool] {message.name}: {message.content}")
                    elif node_name == "verifier" and isinstance(message, AIMessage):
                        print(f"\nAgent: {message.content}")