
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import time
import requests

# Import microphone recording function
from audio_recorder import record_audio

# Import speech recognition function
from stt import transcribe_audio

# Import speech generation and playback
from tts import generate_speech, play_audio


# ===================================
# 2. DEFINE API CONFIGURATION
# ===================================

URL = "http://127.0.0.1:8000/chat"

# Store the conversation session ID.

session_id = None


# ===================================
# 3. COMMUNICATE WITH AI BACKEND
# ===================================

def send_message(message, session_id):

    # Prepare customer message and conversation ID.

    payload = {
        "message": message,
        "session_id": session_id
    }

    # Send the message to our FastAPI backend.

    response = requests.post(
        URL,
        json=payload,
        timeout=120
    )

    # Check whether the API request succeeded.

    response.raise_for_status()

    # Return the JSON response as a dictionary.

    return response.json()


# ===================================
# 4. START VOICE CONVERSATION
# ===================================

if __name__ == "__main__":

    print("AI Business Voice Agent")
    print("Press Enter to speak.")
    print("Type 'exit' to stop.")

    # Introduce the AI agent to the customer.

    greeting = (
        "Hello! I am an AI customer support assistant. "
        "How can I help you today?"
    )

    greeting_file = generate_speech(greeting)

    play_audio(greeting_file)


    # Continue the conversation until the customer exits.

    while True:

        command = input("\nPress Enter to speak: ")

        if command.lower().strip() == "exit":
            break

        try:

            # Step 1: Record customer speech.

            audio_file = record_audio(
                filename="customer.wav",
                duration=5
            )

            start_time = time.perf_counter()


            # Step 2: Convert speech into text.

            message = transcribe_audio(audio_file)

            # Ignore recordings without recognized speech.

            if not message.strip():

                print("No speech detected. Please try again.")

                continue

            print("\nCustomer:", message)


            # Step 3: Send customer message to FastAPI.

            result = send_message(
                message,
                session_id
            )


            # Step 4: Preserve conversation memory.

            session_id = result["session_id"]

            answer = result["response"]

            print("Agent:", answer)

            print("[INTENT]", result["intent"])

            print("[API LATENCY]", result["latency"])


            # Step 5: Convert the AI response into speech.

            response_file = generate_speech(
                answer,
                filename="response.wav"
            )


            # Step 6: Measure response preparation time.

            latency = time.perf_counter() - start_time

            print(
                "[VOICE LATENCY]",
                round(latency, 3),
                "seconds"
            )


            # Step 7: Play the generated response.

            play_audio(response_file)


        except Exception as error:

            print("[ERROR]", error)


    # End the conversation politely.

    goodbye_file = generate_speech(
        "Thank you for contacting us. Goodbye!"
    )

    play_audio(goodbye_file)
