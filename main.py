
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import time

from uuid import uuid4
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import our existing LangGraph agent
from agent_memory import agent


# ===================================
# 2. CREATE FASTAPI APPLICATION
# ===================================

app = FastAPI(
    title="AI Business Calling Agent",
    description="AI customer support agent using Qwen, LangGraph and RAG",
    version="1.0"
)


# ===================================
# 3. DEFINE REQUEST MODEL
# ===================================

# Defines the information expected from the client.
# session_id identifies a particular conversation.
# A new session is created if session_id is not provided.

class ChatRequest(BaseModel):

    message: str
    session_id: str | None = None


# ===================================
# 4. DEFINE RESPONSE MODEL
# ===================================

# Defines the information returned by the API.

class ChatResponse(BaseModel):

    session_id: str
    intent: str
    response: str
    awaiting_order_id: bool
    latency: float


# ===================================
# 5. ROOT ENDPOINT
# ===================================

# This endpoint provides basic application information.

@app.get("/")
def root():

    return {
        "message": "AI Business Calling Agent",
        "version": "1.0",
        "status": "running"
    }


# ===================================
# 6. HEALTH CHECK ENDPOINT
# ===================================

# Checks whether the backend server is responding.

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# ===================================
# 7. CHAT ENDPOINT
# ===================================

# Receives a customer message, executes the AI agent,
# and returns the generated response.

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    # Remove unnecessary spaces from the message.

    message = request.message.strip()

    # Reject empty customer messages.

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    # Use the existing session ID if provided.
    # Otherwise, generate a new unique session ID.

    session_id = request.session_id or str(uuid4())

    # Connect the session ID to LangGraph's thread ID.
    # This allows each conversation to maintain its own state.

    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    # Record the starting time to measure response latency.

    start_time = time.perf_counter()

    try:

        print("[API] Session:", session_id)
        print("[API] Customer message:", message)

        # Execute our existing LangGraph agent.

        result = agent.invoke(
            {"message": message},
            config=config
        )

        # Calculate the time taken by the AI agent.

        latency = time.perf_counter() - start_time

        # Display debugging information.

        print("[API] Intent:", result["intent"])
        print("[API] Response:", result["response"])
        print("[API] Latency:", round(latency, 3), "seconds")

        # Return the final response as structured data.

        return ChatResponse(
            session_id=session_id,
            intent=result["intent"],
            response=result["response"],
            awaiting_order_id=result.get(
                "awaiting_order_id", False
            ),
            latency=round(latency, 3)
        )

    except Exception as error:

        # Handle unexpected errors without exposing
        # internal technical details to the customer.

        print("[ERROR]", error)

        raise HTTPException(
            status_code=500,
            detail="The AI agent encountered a technical problem"
        )
