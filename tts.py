
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import wave
import subprocess

from pathlib import Path
from piper import PiperVoice


# ===================================
# 2. LOAD VOICE MODEL
# ===================================

BASE_DIR = Path(__file__).resolve().parent

VOICE_PATH = (
    BASE_DIR / "voices" / "en_US-lessac-medium.onnx"
)

print("[TTS] Loading voice model...")

# Load the pretrained Piper voice.

voice = PiperVoice.load(str(VOICE_PATH))

print("[TTS] Voice model loaded successfully.")


# ===================================
# 3. CONVERT TEXT INTO SPEECH
# ===================================

def generate_speech(text, filename="response.wav"):

    print("[TTS] Generating speech...")

    # Generate audio from the supplied text
    # and save it as a WAV file.

    with wave.open(str(filename), "wb") as file:

        voice.synthesize_wav(text, file)

    print("[TTS] Audio saved:", filename)

    return filename


# ===================================
# 4. PLAY GENERATED AUDIO
# ===================================

def play_audio(filename):

    # afplay is the built-in macOS audio player.
    # Wait until audio playback is completed.

    subprocess.run(
        ["afplay", str(filename)],
        check=True
    )


# ===================================
# 5. TEST TEXT-TO-SPEECH
# ===================================

if __name__ == "__main__":

    text = "Hello! I am your AI customer support assistant."

    filename = generate_speech(text)

    play_audio(filename)
