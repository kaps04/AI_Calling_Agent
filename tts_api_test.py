
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import requests
import subprocess

from pathlib import Path


# ===================================
# 2. DEFINE CONFIGURATION
# ===================================

URL = "http://127.0.0.1:8000/synthesize"

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_FILE = BASE_DIR / "api_response.wav"


# ===================================
# 3. TEST TEXT-TO-SPEECH API
# ===================================

def test_synthesis(text):

    # Prepare the text request.

    payload = {
        "text": text
    }

    try:

        # -----------------------------------
        # SEND TEXT TO FASTAPI
        # -----------------------------------

        print("[TEST] Sending text:", text)

        print("[API] Waiting for backend response...")

        response = requests.post(
            URL,
            json=payload,
            timeout=30
        )

        print("[API] Response received")


        # -----------------------------------
        # CHECK BACKEND ERROR
        # -----------------------------------

        if not response.ok:

            print("[STATUS]", response.status_code)

            print("[SERVER ERROR]", response.text)

            return

        response.raise_for_status()

        print("[STATUS]", response.status_code)


        # -----------------------------------
        # VERIFY AUDIO RESPONSE
        # -----------------------------------

        content_type = response.headers.get(
            "Content-Type",
            ""
        )

        print("[CONTENT TYPE]", content_type)

        if "audio/wav" not in content_type:

            print("[ERROR] Invalid audio response")

            return


        # -----------------------------------
        # SAVE GENERATED AUDIO
        # -----------------------------------

        OUTPUT_FILE.write_bytes(
            response.content
        )

        print("[AUDIO] Saved:", OUTPUT_FILE.name)


        # -----------------------------------
        # DISPLAY TTS LATENCY
        # -----------------------------------

        print(
            "[LATENCY]",
            response.headers.get("X-TTS-Latency"),
            "seconds"
        )


        # -----------------------------------
        # PLAY GENERATED AUDIO
        # -----------------------------------

        print("[AUDIO] Playing response...")

        subprocess.run(
            ["afplay", str(OUTPUT_FILE)],
            check=True
        )


    # ===================================
    # HANDLE ERRORS
    # ===================================

    except requests.exceptions.Timeout:

        print("[ERROR] Backend request timed out.")

    except requests.exceptions.ConnectionError:

        print("[ERROR] Cannot connect to FastAPI.")

    except Exception as error:

        print("[ERROR]", error)


# ===================================
# 4. RUN TEST
# ===================================

if __name__ == "__main__":

    print("Text-to-Speech API Test")

    print("Type 'exit' to stop.")

    while True:

        text = input("\nEnter text: ").strip()

        if text.lower() == "exit":

            break

        if not text:

            continue

        test_synthesis(text)
