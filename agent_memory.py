
import re
import ollama

from rag import answer_question
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from intent import classify_intent
from tools import get_order_status


# 1. Define state

# State stores information shared between different nodes.
# LangGraph updates this information as the workflow executes.

# ===================================
# 2. DEFINE AGENT STATE
# ===================================

class AgentState(TypedDict):

    message: str
    intent: str
    previous_intent: str
    order_id: str
    response: str
    awaiting_order_id: bool


# ===================================
# 3. INTENT CLASSIFICATION NODE
# ===================================

def classify_node(state: AgentState):

    # Retrieve the current customer message.

    message = state["message"]

    # Normalize the message for pattern matching.

    cleaned_message = message.strip().upper()

    # Retrieve the intent from the previous conversation turn.

    previous_intent = state.get("intent", "")

    # Check whether the agent is waiting for an order ID.

    awaiting_order_id = state.get(
        "awaiting_order_id",
        False
    )

    print("[MEMORY] Previous intent:", previous_intent)

    print(
        "[MEMORY] Awaiting order ID:",
        awaiting_order_id
    )


    # -----------------------------------
    # CHECK FOR STANDALONE ORDER NUMBER
    # -----------------------------------

    # Examples:
    # 102, ORD-102, It's 102,
    # My order ID is 102

    match = re.fullmatch(
        r"(?:IT['’]S\s+|MY ORDER ID IS\s+)?"
        r"(?:ORD-)?(\d+)[.!]?",
        cleaned_message
    )


    # -----------------------------------
    # CHECK PREVIOUS ORDER CONTEXT
    # -----------------------------------

    if match and (
        awaiting_order_id
        or previous_intent == "order_status"
    ):

        order_id = "ORD-" + match.group(1)

        print("[MEMORY] Order context detected")

        print("[DEBUG] Order ID:", order_id)

        return {
            "intent": "order_status",
            "previous_intent": previous_intent,
            "order_id": order_id,
            "awaiting_order_id": False
        }


    # -----------------------------------
    # CHECK EXPLICIT ORDER ID
    # -----------------------------------

    # Example: ORD-105

    explicit_match = re.fullmatch(
        r"ORD-\d+[.!]?",
        cleaned_message
    )

    if explicit_match:

        order_id = explicit_match.group().rstrip(".!")

        return {
            "intent": "order_status",
            "previous_intent": previous_intent,
            "order_id": order_id,
            "awaiting_order_id": False
        }


    # -----------------------------------
    # HANDLE AMBIGUOUS NUMERIC INPUT
    # -----------------------------------

    # Do not send standalone numbers to RAG
    # when no relevant order context exists.

    if match:

        print("[DEBUG] Ambiguous numeric input")

        return {
            "intent": "clarification",
            "previous_intent": previous_intent,
            "order_id": "",
            "awaiting_order_id": False
        }


    # -----------------------------------
    # NORMAL LLM CLASSIFICATION
    # -----------------------------------

    intent = classify_intent(message)

    print("[DEBUG] Detected intent:", intent)

    # Extract an explicit order ID from the sentence.

    match = re.search(
        r"ORD-\d+",
        cleaned_message
    )

    return {
        "intent": intent,
        "previous_intent": previous_intent,
        "order_id": match.group() if match else "",
        "awaiting_order_id": (
            awaiting_order_id
            if intent == "chitchat"
            else False
        )
    }


# 3. Order status node

def order_node(state: AgentState):

    # Retrieve the order ID from the current state.

    order_id = state.get("order_id", "")

    # If the order ID is missing, ask the customer.
    # Set awaiting_order_id to True so the agent remembers
    # what information it needs in the next conversation turn.

    if not order_id:

        return {
            "response": "Could you provide your order ID?",
            "awaiting_order_id": True
        }

    # Execute the business tool to retrieve the actual
    # order status from the SQLite database.

    status = get_order_status(order_id)

    print("[DEBUG] Order ID:", order_id)
    print("[DEBUG] Database result:", status)

    # If the order does not exist, ask the customer
    # to provide a corrected order ID.

    if status == "Order not found":

        return {
            "response": "Order not found. Please check your order ID.",
            "order_id": "",
            "awaiting_order_id": True
        }

    # Return verified database information.
    # We do not use the LLM here to avoid inventing order details.

    return {
        "response": f"Your order {order_id} has status: {status}.",
        "awaiting_order_id": False
    }


# 4. Refund node

def refund_node(state: AgentState):

    # Use RAG to retrieve relevant refund and return
    # policy information from the company knowledge base.

    print("[ROUTE] Refund and return policy")

    answer = answer_question(state["message"])

    return {
        "response": answer,
        "awaiting_order_id": False
    }


# 5. Business hours node

def hours_node(state: AgentState):

    # Retrieve company opening hours using RAG
    # instead of hardcoding business hours.

    print("[ROUTE] Business hours")

    answer = answer_question(state["message"])

    return {
        "response": answer,
        "awaiting_order_id": False
    }


# 6. Human support node

def human_node(state: AgentState):

    # Handle customers who request human assistance.
    # Actual call transfer will be implemented later.

    print("[ROUTE] Human support")

    return {
        "response": "Your request requires human assistance.",
        "awaiting_order_id": False
    }


# 7. General response node

def general_node(state: AgentState):

    # Handle general business questions such as
    # payment methods, shipping costs and delivery policies.

    print("[ROUTE] Company knowledge base")

    # Retrieve relevant documents and generate a response.

    answer = answer_question(state["message"])

    return {
        "response": answer,
        "awaiting_order_id": False
    }


# 8. Chitchat node

def chitchat_node(state: AgentState):

    # Handle greetings, thanks and casual conversation.
    # These messages do not require database access or RAG.

    print("[ROUTE] Casual conversation")

    # Send the customer message directly to the local LLM.

    response = ollama.chat(
        model="qwen2.5:1.5b",
        messages=[
            {
                "role": "system",
                "content": """
You are a friendly AI customer support assistant.

Respond naturally and politely.
Keep your response short and conversational.
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

    # Extract the generated text from the LLM response.

    answer = response["message"]["content"].strip()

    # Preserve the previous pending order inquiry
    # if the customer temporarily switches to casual conversation.

    return {
        "response": answer,
        "awaiting_order_id": state.get(
            "awaiting_order_id", False
        )
    }

# CLARIFICATION NODE
# ===================================

def clarification_node(state: AgentState):

    # Handle ambiguous customer messages
    # without retrieving unrelated information.

    print("[ROUTE] Clarification required")

    return {
        "response": (
            "Could you please clarify your request? "
            "Are you referring to an order ID?"
        ),
        "awaiting_order_id": False
    }


# 9. Routing function

def route_intent(state: AgentState):

    # Return the detected intent.
    # LangGraph uses this value to select the next node.

    return state["intent"]


# 10. Build workflow

# Create a LangGraph workflow using our AgentState schema.

workflow = StateGraph(AgentState)


# Register all nodes.
# Each node has a name and a corresponding Python function.

workflow.add_node("classify", classify_node)
workflow.add_node("order", order_node)
workflow.add_node("refund", refund_node)
workflow.add_node("hours", hours_node)
workflow.add_node("human", human_node)
workflow.add_node("general", general_node)
workflow.add_node("chitchat", chitchat_node)
workflow.add_node("clarification", clarification_node)


# Define the starting point.
# Every customer message first enters the classification node.

workflow.add_edge(START, "classify")







# Define conditional edges.
# The detected intent determines which node executes next.

workflow.add_conditional_edges(
    "classify",
    route_intent,
    {
        "order_status": "order",
        "refund": "refund",
        "business_hours": "hours",
        "human_support": "human",
        "general": "general",
        "chitchat": "chitchat",
        "clarification": "clarification"
    }
)


# Define ending edges.
# After a selected node generates a response,
# the workflow finishes for the current conversation turn.

for node in [
    "order",
    "refund",
    "hours",
    "human",
    "general",
    "chitchat",
    "clarification"
]:
    
    workflow.add_edge(node, END)


# 11. Add conversation memory

# InMemorySaver stores conversation state in RAM
# between multiple executions of the graph.

memory = InMemorySaver()


# Compile the workflow with checkpointing enabled.
# The compiled graph is our executable AI agent.

agent = workflow.compile(checkpointer=memory)


# 12. Start conversation

# This section executes only when this file is run directly.
# It does not execute when another Python file imports the agent.

if __name__ == "__main__":

    # Thread ID identifies a particular conversation.
    # Different thread IDs can maintain separate states.

    config = {
        "configurable": {
            "thread_id": "customer_001"
        }
    }

    print("AI Customer Support Agent with Memory")
    print("Type 'exit' to stop.")

    # Keep the conversation running until the customer exits.

    while True:

        message = input("\nCustomer: ")

        # Stop the program when the customer types exit.

        if message.lower().strip() == "exit":
            break

        # Ignore empty messages.

        if not message.strip():
            continue

        # Execute the graph using the new customer message.
        # LangGraph retrieves previous state using the thread ID.

        result = agent.invoke(
            {"message": message},
            config=config
        )

        # Display the final response.

        print("Agent:", result["response"])

        # Display conversation state for debugging.

        print(
            "[STATE] Awaiting order ID:",
            result.get("awaiting_order_id", False)
        )
