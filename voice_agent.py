
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import time
import requests

# Import automatic microphone recording.

from audio_recorder import record_until_silence

# Import Speech-to-Text.

from stt import transcribe_audio

# Import Text-to-Speech and audio playback.

from tts import generate_speech, play_audio

# Import spoken order ID normalization.

from speech_utils import normalize_order_id


# ===================================
# 2. DEFINE API CONFIGURATION
# ===================================

URL = "http://127.0.0.1:8000/chat"

# Store the session ID to maintain
# conversation memory across multiple requests.

session_id = None

# Track whether the agent is waiting
# for the customer to provide an order ID.

awaiting_order_id = False


# ===================================
# 3. COMMUNICATE WITH AI BACKEND
# ===================================

def send_message(message, session_id):

    # Prepare the customer message
    # and conversation session ID.

    payload = {
        "message": message,
        "session_id": session_id
    }

    # Send an HTTP POST request to FastAPI.

    response = requests.post(
        URL,
        json=payload,
        timeout=120
    )

    # Check whether the request succeeded.

    response.raise_for_status()

    # Convert the JSON response into a dictionary.

    return response.json()


# ===================================
# 4. SPEAK AI RESPONSE
# ===================================

def speak(text):

    # Convert text into a WAV audio file.

    filename = generate_speech(
        text,
        filename="response.wav"
    )

    # Play the generated audio.

    play_audio(filename)


# ===================================
# 5. DETECT CONVERSATION END
# ===================================

def should_end_conversation(message):

    # Define common spoken exit commands.

    exit_commands = [
        "goodbye",
        "good bye",
        "bye",
        "exit",
        "end call",
        "end the call",
        "hang up",
        "thank you goodbye",
        "thank you bye",
        "thanks goodbye",
        "bye bye"
    ]

    # Normalize the customer message.

    cleaned = message.lower()

    # Remove common punctuation.

    for symbol in [",", ".", "!", "?"]:

        cleaned = cleaned.replace(symbol, " ")

    # Remove unnecessary spaces.

    cleaned = " ".join(cleaned.split())

    # Check whether the customer wants
    # to terminate the conversation.

    return cleaned in exit_commands


# ===================================
# 6. START VOICE CONVERSATION
# ===================================

if __name__ == "__main__":

    print("=" * 45)
    print("AI Business Voice Agent")
    print("Automatic Conversation Mode")
    print("Say 'goodbye' to end the conversation.")
    print("Press Ctrl+C to stop manually.")
    print("=" * 45)

    # Introduce the AI agent to the customer.

    greeting = (
        "Hello! I am your AI customer support assistant. "
        "How can I help you today?"
    )

    print("\nAgent:", greeting)

    try:

        speak(greeting)

        # Continue listening until the customer
        # terminates the conversation.

        while True:

            # -----------------------------------
            # STEP 1: RECORD CUSTOMER SPEECH
            # -----------------------------------

            # Automatically start recording when
            # speech is detected and stop after silence.

            audio_file = record_until_silence(
                filename="customer.wav"
            )

            # Continue listening if no speech is detected.

            if audio_file is None:

                continue

            # Record the starting time to measure
            # response preparation latency.

            start_time = time.perf_counter()


            # -----------------------------------
            # STEP 2: CONVERT SPEECH INTO TEXT
            # -----------------------------------

            message = transcribe_audio(audio_file)

            # Ignore empty transcriptions.

            if not message.strip():

                print("[STT] No speech recognized.")

                continue

            print("\nCustomer:", message)


            # -----------------------------------
            # STEP 3: CHECK CONVERSATION END
            # -----------------------------------

            if should_end_conversation(message):

                print("[CALL] Customer ended conversation.")

                break


            # -----------------------------------
            # STEP 4: NORMALIZE SPOKEN ORDER ID
            # -----------------------------------

            # Apply normalization only when the
            # backend is expecting an order ID.

            if awaiting_order_id:

                original_message = message

                message = normalize_order_id(message)

                print("[ORIGINAL]", original_message)

                print("[NORMALIZED]", message)


            # -----------------------------------
            # STEP 5: SEND MESSAGE TO FASTAPI
            # -----------------------------------

            result = send_message(
                message,
                session_id
            )


            # -----------------------------------
            # STEP 6: UPDATE CONVERSATION STATE
            # -----------------------------------

            # Preserve the session ID for memory.

            session_id = result["session_id"]

            # Check whether the agent is waiting
            # for an order ID.

            awaiting_order_id = result.get(
                "awaiting_order_id",
                False
            )

            # Extract the AI-generated response.

            answer = result["response"]

            print("\nAgent:", answer)

            print("[INTENT]", result["intent"])

            print("[SESSION]", session_id)

            print(
                "[AWAITING ORDER ID]",
                awaiting_order_id
            )

            print(
                "[API LATENCY]",
                result["latency"],
                "seconds"
            )


            # -----------------------------------
            # STEP 7: GENERATE SPEECH
            # -----------------------------------

            response_file = generate_speech(
                answer,
                filename="response.wav"
            )


            # -----------------------------------
            # STEP 8: MEASURE VOICE LATENCY
            # -----------------------------------

            latency = time.perf_counter() - start_time

            print(
                "[VOICE LATENCY]",
                round(latency, 3),
                "seconds"
            )


            # -----------------------------------
            # STEP 9: PLAY AI RESPONSE
            # -----------------------------------

            play_audio(response_file)

            # Once playback is completed, the loop
            # automatically starts listening again.


    # ===================================
    # 7. HANDLE EXCEPTIONS
    # ===================================

    except KeyboardInterrupt:

        print("\n[CALL] Conversation interrupted.")


    except requests.exceptions.RequestException as error:

        print("[API ERROR]", error)


    except Exception as error:

        print("[ERROR]", error)


    # ===================================
    # 8. END CONVERSATION
    # ===================================

    goodbye = (
        "Thank you for contacting us. Goodbye!"
    )

    print("\nAgent:", goodbye)

    try:

        speak(goodbye)

    except Exception as error:

        print("[TTS ERROR]", error)

    print("[CALL] Conversation ended.")
