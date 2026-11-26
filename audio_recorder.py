
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import wave
import time
import numpy as np
import sounddevice as sd

from collections import deque

# Import speech detection from vad.py

from vad import is_speech, ENERGY_THRESHOLD


# ===================================
# 2. AUDIO CONFIGURATION
# ===================================

SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 5

# Process audio in 30-millisecond chunks.

CHUNK_DURATION = 0.03

CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

# Stop recording after continuous silence.

SILENCE_DURATION = 1.2

# Minimum duration required to confirm speech.

MIN_SPEECH_DURATION = 0.15

# Preserve audio before speech detection.

PRE_ROLL_DURATION = 0.3

# Prevent indefinite waiting and recording.

MAX_WAIT_TIME = 20
MAX_RECORD_TIME = 30


# ===================================
# 3. SAVE AUDIO FILE
# ===================================

def save_audio(audio, filename):

    # Save audio samples into a WAV file.

    with wave.open(str(filename), "wb") as file:

        file.setnchannels(CHANNELS)

        # int16 requires 2 bytes per sample.

        file.setsampwidth(2)

        file.setframerate(SAMPLE_RATE)

        file.writeframes(audio.tobytes())

    print("[AUDIO] Saved:", filename)

    return filename


# ===================================
# 4. FIXED-DURATION RECORDING
# ===================================

def record_audio(filename="customer.wav", duration=DURATION):

    # Original recording function.
    # Retained for independent testing.

    print("[AUDIO] Recording... Speak now.")

    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16"
    )

    # Wait until recording is completed.

    sd.wait()

    print("[AUDIO] Recording completed.")

    return save_audio(audio, filename)


# ===================================
# 5. AUTOMATIC SPEECH RECORDING
# ===================================

def record_until_silence(
    filename="customer.wav",
    threshold=ENERGY_THRESHOLD
):

    print("[AUDIO] Listening...")

    # Store recorded audio chunks.

    recorded_chunks = []

    # Store recent audio before speech starts.
    # This prevents losing the beginning of a word.

    pre_roll = deque(
        maxlen=int(PRE_ROLL_DURATION / CHUNK_DURATION)
    )

    # Initialize speech detection variables.

    speech_started = False

    speech_chunks = 0
    silent_chunks = 0

    # Convert time durations into chunk counts.

    min_speech_chunks = int(
        MIN_SPEECH_DURATION / CHUNK_DURATION
    )

    max_silent_chunks = int(
        SILENCE_DURATION / CHUNK_DURATION
    )

    # Track waiting and recording times.

    waiting_start = time.monotonic()

    recording_start = None


    # Open a continuous microphone input stream.

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=CHUNK_SIZE
    ) as stream:

        while True:

            # Read one audio chunk.

            audio_chunk, overflowed = stream.read(
                CHUNK_SIZE
            )

            if overflowed:

                print("[AUDIO] Input overflow detected.")

            # Determine whether the chunk contains speech.

            speaking = is_speech(
                audio_chunk,
                threshold
            )


            # -----------------------------------
            # WAIT FOR SPEECH TO START
            # -----------------------------------

            if not speech_started:

                # Store recent audio in the rolling buffer.

                pre_roll.append(audio_chunk.copy())

                if speaking:

                    speech_chunks += 1

                else:

                    speech_chunks = 0

                # Confirm that speech has started.

                if speech_chunks >= min_speech_chunks:

                    speech_started = True

                    recording_start = time.monotonic()

                    # Preserve audio before speech detection.

                    recorded_chunks.extend(pre_roll)

                    print("[VAD] Speech detected.")

                # Stop waiting if nobody speaks.

                elif (
                    time.monotonic() - waiting_start
                    >= MAX_WAIT_TIME
                ):

                    print("[VAD] No speech detected.")

                    return None


            # -----------------------------------
            # RECORD UNTIL SPEECH ENDS
            # -----------------------------------

            else:

                # Store the current audio chunk.

                recorded_chunks.append(
                    audio_chunk.copy()
                )

                if speaking:

                    # Reset silence counter when
                    # speech is detected.

                    silent_chunks = 0

                else:

                    # Increase silence counter.

                    silent_chunks += 1

                # Stop recording after continuous silence.

                if silent_chunks >= max_silent_chunks:

                    print("[VAD] End of speech detected.")

                    break

                # Limit maximum recording duration.

                if (
                    time.monotonic() - recording_start
                    >= MAX_RECORD_TIME
                ):

                    print("[VAD] Maximum recording reached.")

                    break


    # Check whether any audio was recorded.

    if not recorded_chunks:

        return None

    # Combine individual chunks into one audio array.

    audio = np.concatenate(
        recorded_chunks,
        axis=0
    )

    # Save the complete audio recording.

    return save_audio(audio, filename)


# ===================================
# 6. TEST AUTOMATIC RECORDING
# ===================================

if __name__ == "__main__":

    print("Automatic Speech Recording")
    print("Speak naturally after listening starts.")

    filename = record_until_silence()

    if filename:

        print("[AUDIO] Recording successful.")
