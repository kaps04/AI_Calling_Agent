
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import requests


# ===================================
# 2. DEFINE API ADDRESS
# ===================================

URL = "http://127.0.0.1:8000/chat"

# Store the session ID across conversation turns.

session_id = None


# ===================================
# 3. START CONVERSATION
# ===================================

print("AI Agent API Client")
print("Type 'exit' to stop.")

while True:

    message = input("\nCustomer: ").strip()

    if message.lower() == "exit":
        break

    if not message:
        continue

    # Prepare the JSON request body.

    payload = {
        "message": message,
        "session_id": session_id
    }

    try:

        # Send an HTTP POST request to FastAPI.

        response = requests.post(
            URL,
            json=payload,
            timeout=120
        )

        # Check whether the request was successful.

        response.raise_for_status()

        # Convert the JSON response into a Python dictionary.

        result = response.json()

        # Save the session ID for subsequent messages.

        session_id = result["session_id"]

        # Display the response and execution details.

        print("Agent:", result["response"])
        print("[INTENT]", result["intent"])
        print("[SESSION]", session_id)
        print("[LATENCY]", result["latency"], "seconds")

    except requests.exceptions.RequestException as error:

        print("[ERROR]", error)
