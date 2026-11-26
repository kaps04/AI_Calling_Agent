
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import wave
import sounddevice as sd


# ===================================
# 2. AUDIO CONFIGURATION
# ===================================

SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 5


# ===================================
# 3. RECORD AUDIO
# ===================================

def record_audio(filename="customer.wav", duration=DURATION):

    print("[AUDIO] Recording... Speak now.")

    # Record audio from the default microphone.
    # The recording is stored as a NumPy array.

    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16"
    )

    # Wait until the recording is completed.

    sd.wait()

    print("[AUDIO] Recording completed.")

    # Save the recorded samples as a WAV file.

    with wave.open(str(filename), "wb") as file:

        file.setnchannels(CHANNELS)

        # int16 uses 2 bytes per sample.

        file.setsampwidth(2)

        file.setframerate(SAMPLE_RATE)

        file.writeframes(audio.tobytes())

    print("[AUDIO] Saved:", filename)

    return filename


# ===================================
# 4. TEST AUDIO RECORDING
# ===================================

if __name__ == "__main__":

    input("Press Enter to start recording...")

    record_audio()
