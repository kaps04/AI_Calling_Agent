
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import re
import ollama

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# Import intent classification from intent.py
from intent import classify_intent

# Import business tool from tools.py
from tools import get_order_status


# ===================================
# 2. DEFINE AGENT STATE
# ===================================

# AgentState defines the information shared
# between different nodes in the LangGraph workflow.

class AgentState(TypedDict):

    message: str     # Customer's input message
    intent: str      # Detected customer intent
    order_id: str    # Extracted order ID
    response: str    # Final response to the customer


# ===================================
# 3. INTENT CLASSIFICATION NODE
# ===================================

def classify_node(state: AgentState):

    # Retrieve the customer message and classify
    # its intent using the local Qwen LLM.

    intent = classify_intent(state["message"])

    print("[DEBUG] Detected intent:", intent)

    # Update the intent in the agent state.

    return {"intent": intent}


# ===================================
# 4. ORDER STATUS NODE
# ===================================

def order_node(state: AgentState):

    # Retrieve the customer message.

    message = state["message"]

    # Extract the order ID using a regular expression.
    # Example: ORD-102, ORD-103, ord-104

    match = re.search(r"ORD-\d+", message.upper())

    # If no order ID is found, request it from the customer.

    if not match:

        return {
            "response": "Could you provide your order ID?"
        }

    # Extract the matched order ID.

    order_id = match.group()

    print("[DEBUG] Order ID:", order_id)

    # Execute the business tool to retrieve
    # the actual order status from SQLite.

    status = get_order_status(order_id)

    print("[DEBUG] Database result:", status)

    # Check whether the order exists in the database.

    if status == "Order not found":

        response = "I could not find that order."

    else:

        response = f"Your order {order_id} has status: {status}."

    # Update the order ID and response in the state.

    return {
        "order_id": order_id,
        "response": response
    }


# ===================================
# 5. REFUND NODE
# ===================================

def refund_node(state: AgentState):

    # Handle refund and return-related questions.
    # For this basic version, the response is hardcoded.
    # RAG-based retrieval is implemented in agent_memory.py.

    print("[ROUTE] Refund and return policy")

    return {
        "response": "Eligible products can be returned within 30 days."
    }


# ===================================
# 6. BUSINESS HOURS NODE
# ===================================

def hours_node(state: AgentState):

    # Provide the company's operating hours.
    # This information is hardcoded in the basic version.

    print("[ROUTE] Business hours")

    return {
        "response": "We are open Monday to Friday, 9 AM to 5 PM."
    }


# ===================================
# 7. HUMAN SUPPORT NODE
# ===================================

def human_node(state: AgentState):

    # Handle requests that require human assistance.
    # Actual call transfer is not implemented yet.

    print("[ROUTE] Human support")

    return {
        "response": "Your request requires assistance from our support team."
    }


# ===================================
# 8. GENERAL RESPONSE NODE
# ===================================

def general_node(state: AgentState):

    # Provide a fallback response for general questions.
    # This version does not retrieve company documents.

    print("[ROUTE] General inquiry")

    return {
        "response": "I can help with orders, returns and business hours."
    }


# ===================================
# 9. CHITCHAT RESPONSE NODE
# ===================================

def chitchat_node(state: AgentState):

    # Handle greetings, thanks and casual conversation.
    # No database access is required for these messages.

    print("[ROUTE] Casual conversation")

    # Send the customer message directly to Qwen.

    response = ollama.chat(
        model="qwen2.5:1.5b",
        messages=[
            {
                "role": "system",
                "content": """
You are a friendly AI customer support assistant.

Respond naturally and politely.
Keep your response short.
Do not invent company information.
If appropriate, ask how you can help.
Stay focused on customer support.
"""
            },
            {
                "role": "user",
                "content": state["message"]
            }
        ],
        options={"temperature": 0}
    )

    # Extract the generated response from the LLM.

    answer = response["message"]["content"].strip()

    # Return the response to the agent state.

    return {
        "response": answer
    }


# ===================================
# 10. ROUTING FUNCTION
# ===================================

def route_intent(state: AgentState):

    # Return the detected intent.
    # LangGraph uses this value to determine
    # which node should execute next.

    return state["intent"]


# ===================================
# 11. BUILD LANGGRAPH
# ===================================

# Create a workflow using the AgentState schema.

workflow = StateGraph(AgentState)


# Register nodes.
# Each node name is connected to a Python function.

workflow.add_node("classify", classify_node)
workflow.add_node("order", order_node)
workflow.add_node("refund", refund_node)
workflow.add_node("hours", hours_node)
workflow.add_node("human", human_node)
workflow.add_node("general", general_node)
workflow.add_node("chitchat", chitchat_node)


# Starting point.
# Every customer message first enters
# the intent classification node.

workflow.add_edge(START, "classify")


# Conditional routing.
# Based on the detected intent, LangGraph
# selects the corresponding node.

workflow.add_conditional_edges(
    "classify",
    route_intent,
    {
        "order_status": "order",
        "refund": "refund",
        "business_hours": "hours",
        "human_support": "human",
        "general": "general",
        "chitchat": "chitchat"
    }
)


# Ending points.
# After the selected node generates a response,
# the workflow ends for the current request.

workflow.add_edge("order", END)
workflow.add_edge("refund", END)
workflow.add_edge("hours", END)
workflow.add_edge("human", END)
workflow.add_edge("general", END)
workflow.add_edge("chitchat", END)


# Compile the graph.
# Convert the defined workflow into an executable agent.
# No checkpointer is provided, so there is no
# conversation memory between separate invocations.

agent = workflow.compile()


# ===================================
# 12. RUN THE AGENT
# ===================================

# This section executes only when agent.py
# is run directly from the terminal.

if __name__ == "__main__":

    print("AI Customer Support Agent")
    print("Type 'exit' to stop.")

    # Continuously receive customer messages.

    while True:

        message = input("\nCustomer: ")

        # Stop the program if the customer types exit.

        if message.lower().strip() == "exit":
            break

        # Ignore empty customer messages.

        if not message.strip():
            continue

        # Execute the LangGraph workflow.
        # A new state is created for every customer message.

        result = agent.invoke({
            "message": message,
            "intent": "",
            "order_id": "",
            "response": ""
        })

        # Display the final response to the customer.

        print("Agent:", result["response"])
