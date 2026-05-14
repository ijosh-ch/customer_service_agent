import warnings
from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.filterwarnings(
    "ignore",
    category=LangChainPendingDeprecationWarning
)

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
    return mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678", 
            database="customer_service", 
        )

# ==========================================
# 2. DEFINE TOOLS [cite: 68-80]
# ==========================================
import mysql.connector
from langchain_core.tools import tool

# Assuming your connection function from earlier

@tool
def order_lookup(order_id: int, config: RunnableConfig) -> str:
    """Retrieve order details for a specific order ID."""
    verify_customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        # dictionary=True returns the row as a dict, making it easy for the LLM to read
        cursor = conn.cursor(dictionary=True) 
        
        query = "SELECT * FROM orders WHERE order_id = %s AND customer_id = %s;"
        cursor.execute(query, (order_id, verify_customer_id))
        result = cursor.fetchone()
        
        if result:
            # Convert datetime objects to string if necessary, but LLM usually handles dict stringification well
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
        
        # CRITICAL: Commit the transaction to save changes to MySQL
        conn.commit()
        
        # Check if the row was actually updated (in case a bad order_id was passed)
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
        
        # CRITICAL: Commit the transaction to save changes to MySQL
        conn.commit()
        
        return f"Success: Complaint logged for order {order_id}."
        
    except mysql.connector.Error as err:
        return f"Database error occurred: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@tool
def read_long_term_memory(config: RunnableConfig) -> str:
    """Retrieve all long-term memory records (preferences, past issues) stored for this customer."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT `key`, value, created_at FROM customer_memory WHERE customer_id = %s ORDER BY created_at DESC;"
        cursor.execute(query, (customer_id,))
        results = cursor.fetchall()
        if results:
            lines = [f"- {r['key']}: {r['value']} (saved: {r['created_at']})" for r in results]
            return f"Long-term memory for customer {customer_id}:\n" + "\n".join(lines)
        return f"No long-term memory found for customer {customer_id}."
    except mysql.connector.Error as err:
        return f"Database error: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


@tool
def write_long_term_memory(key: str, value: str, config: RunnableConfig) -> str:
    """Save a customer preference or important note to long-term memory (MySQL customer_memory table)."""
    customer_id = config["configurable"]["customer_id"]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO customer_memory (customer_id, `key`, value) VALUES (%s, %s, %s);"
        cursor.execute(query, (customer_id, key, value))
        conn.commit()
        return f"Saved to long-term memory: '{key}' = '{value}' for customer {customer_id}."
    except mysql.connector.Error as err:
        return f"Database error: {err}"
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


# Bind tools to the LLM so it knows how to use them
tools = [order_lookup, customer_profile, request_refund, log_complaint,
         read_long_term_memory, write_long_term_memory]
llm_with_tools = llm.bind_tools(tools)

# ==========================================
# 3. DEFINE THE STATE [cite: 118-120]
# ==========================================
class AgentState(TypedDict):
    # Tracks conversation history and maintains context across turns [cite: 121-122]
    messages: Annotated[list, add_messages]

# ==========================================
# 4. DEFINE THE NODES [cite: 36-67]
# ==========================================

def planner_node(state: AgentState):
    """
    Extracts intent, extracts entities, and generates an execution plan [cite: 37-40].
    """
    system_prompt = SystemMessage(
        content="You are an intelligent customer service agent. "
                "Analyze the user's input, extract intents (refund, tracking, complaint, memory query, preference), "
                "and extract entities (order_id, product, preference). "
                "Available tools: order_lookup, customer_profile, request_refund, log_complaint, "
                "read_long_term_memory, write_long_term_memory. "
                "For multi-step requests (e.g. 'refund if delivered'), first call order_lookup, then decide. "
                "For personalization queries (e.g. 'late again'), call read_long_term_memory first to check history. "
                "When a user asks to remember a preference, call write_long_term_memory."
    )
    # The LLM will either return a standard response or a tool call (the "Plan")
    response = llm_with_tools.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

def verifier_node(state: AgentState):
    """
    Ensures correctness, prevents hallucinations, and enforces policy compliance [cite: 65-67].
    """
    # Grab the most recent message
    last_message = state["messages"][-1]
    
    # Simple verification prompt using the base LLM (no tools needed here)
    verify_prompt = SystemMessage(
        content="You are a strict compliance verifier for a customer service agent. "
                "Review the proposed response. Ensure it does not hallucinate data, "
                "is polite, and complies with standard refund/complaint policies. "
                "If it is good, output the exact response. If it violates policy, rewrite it safely."
    )
    
    # We pass the conversation context to the verifier
    verified_response = llm.invoke([verify_prompt] + state["messages"])
    return {"messages": [verified_response]}

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
# 6. BUILD THE GRAPH [cite: 21-35]
# ==========================================
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("tools", ToolNode(tools)) # LangGraph's prebuilt tool execution node
workflow.add_node("verifier", verifier_node)

# Add Edges to match the specification
workflow.add_edge(START, "planner")
workflow.add_conditional_edges("planner", route_planner_output)
workflow.add_edge("tools", "verifier") # Tool Node output implicitly acts as Memory Update [cite: 52, 56]
workflow.add_edge("verifier", END)

# Compile with Short-Term Memory Checkpointer
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# ==========================================
# 7. RUN THE AGENT (Example Test) [cite: 133-144]
# ==========================================
if __name__ == "__main__":
    # Create a unique thread ID for the session memory
    config = {"configurable": {"thread_id": "customer_session_001", "customer_id": 2}}
    
    # User Input
    user_query = "where is my orders 1001 and 1002?" # [cite: 134]
    print(f"User: {user_query}\n")
    
    # Stream the execution to see the ReAct steps [cite: 135-142]
    events = app.stream(
        {"messages": [HumanMessage(content=user_query)]}, 
        config, 
        stream_mode="values"
    )
    
    for event in events:
        message = event["messages"][-1]
        if isinstance(message, AIMessage) and message.tool_calls:
            print(f"[Planner] Decided to call tools: {[t['name'] for t in message.tool_calls]}")
        elif message.type == "tool":
            print(f"[Tool Execution] {message.name}: {message.content}")
        elif isinstance(message, AIMessage) and not message.tool_calls:
             print(f"\n[Final Response from Verifier]: {message.content}")