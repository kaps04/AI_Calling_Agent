
# ===================================
# 1. IMPORT LIBRARIES
# ===================================

import time
import tempfile
import traceback

from uuid import uuid4
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi import UploadFile, File
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

# Import our existing LangGraph agent.

from agent_memory import agent

# Import Speech-to-Text module.

from stt import transcribe_audio

# Import Text-to-Speech module.

from tts import generate_speech


# ===================================
# 2. CREATE FASTAPI APPLICATION
# ===================================

app = FastAPI(
    title="AI Business Calling Agent",
    description=(
        "AI customer support agent using "
        "Qwen, LangGraph and RAG"
    ),
    version="1.0"
)


# ===================================
# 3. CONFIGURE CORS
# ===================================

# Allow our React frontend to communicate
# with the FastAPI backend.

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],

    allow_credentials=False,

    allow_methods=["GET", "POST"],

    allow_headers=["*"],

    # Allow React to read TTS latency.

    expose_headers=["X-TTS-Latency"]
)


# ===================================
# 4. DEFINE REQUEST AND RESPONSE MODELS
# ===================================

# Define the information expected from
# the customer through the chat endpoint.

class ChatRequest(BaseModel):

    message: str

    session_id: str | None = None


# Define the information returned
# by the chat endpoint.

class ChatResponse(BaseModel):

    session_id: str

    intent: str

    response: str

    awaiting_order_id: bool

    latency: float


# Define the information expected
# by the Text-to-Speech endpoint.

class TTSRequest(BaseModel):

    text: str


# ===================================
# 5. ROOT ENDPOINT
# ===================================

@app.get("/")
def root():

    # Return basic application information.

    return {
        "message": "AI Business Calling Agent",
        "version": "1.0",
        "status": "running"
    }


# ===================================
# 6. HEALTH CHECK ENDPOINT
# ===================================

@app.get("/health")
def health_check():

    # Check whether the backend is responding.

    return {
        "status": "healthy"
    }


# ===================================
# 7. CHAT ENDPOINT
# ===================================

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    # Remove unnecessary spaces.

    message = request.message.strip()

    # Reject empty customer messages.

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )


    # -----------------------------------
    # 7.1. MANAGE CONVERSATION SESSION
    # -----------------------------------

    # Use the existing session ID or
    # generate a new unique session ID.

    session_id = request.session_id or str(uuid4())

    # Connect the session ID to LangGraph's
    # thread ID for conversation memory.

    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    # Record the starting time.

    start_time = time.perf_counter()

    try:

        print("[API] Session:", session_id)

        print("[API] Customer message:", message)


        # -----------------------------------
        # 7.2. EXECUTE LANGGRAPH AGENT
        # -----------------------------------

        result = agent.invoke(
            {"message": message},
            config=config
        )


        # -----------------------------------
        # 7.3. CALCULATE API LATENCY
        # -----------------------------------

        latency = time.perf_counter() - start_time

        print("[API] Intent:", result["intent"])

        print("[API] Response:", result["response"])

        print(
            "[API] Latency:",
            round(latency, 3),
            "seconds"
        )


        # -----------------------------------
        # 7.4. RETURN CHAT RESPONSE
        # -----------------------------------

        return ChatResponse(

            session_id=session_id,

            intent=result["intent"],

            response=result["response"],

            awaiting_order_id=result.get(
                "awaiting_order_id",
                False
            ),

            latency=round(latency, 3)
        )


    # -----------------------------------
    # 7.5. HANDLE CHAT ERRORS
    # -----------------------------------

    except Exception as error:

        print("[CHAT API ERROR]", error)

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ===================================
# 8. SPEECH-TO-TEXT API ENDPOINT
# ===================================

@app.post("/transcribe")
def transcribe(file: UploadFile = File(...)):

    # Record the starting time.

    start_time = time.perf_counter()

    # Store the temporary audio file path.

    audio_path = None

    # Maximum accepted audio file size: 10 MB.

    max_size = 10 * 1024 * 1024

    try:

        # -----------------------------------
        # 8.1. RECEIVE CUSTOMER AUDIO
        # -----------------------------------

        print("[STT API] Received:", file.filename)

        # Read uploaded audio with a size limit.

        audio_data = file.file.read(max_size + 1)

        # Reject empty audio files.

        if not audio_data:

            raise HTTPException(
                status_code=400,
                detail="Empty audio file"
            )

        # Reject excessively large audio files.

        if len(audio_data) > max_size:

            raise HTTPException(
                status_code=413,
                detail="Audio file is too large"
            )


        # -----------------------------------
        # 8.2. CHECK AUDIO FORMAT
        # -----------------------------------

        suffix = Path(
            file.filename or ""
        ).suffix.lower()

        allowed_formats = {
            ".wav",
            ".webm",
            ".mp3",
            ".ogg",
            ".m4a",
            ".mp4"
        }

        if suffix not in allowed_formats:

            raise HTTPException(
                status_code=415,
                detail="Unsupported audio format"
            )


        # -----------------------------------
        # 8.3. CREATE TEMPORARY AUDIO FILE
        # -----------------------------------

        with tempfile.NamedTemporaryFile(

            suffix=suffix,

            delete=False

        ) as temporary_file:

            audio_path = temporary_file.name

            temporary_file.write(audio_data)

        print(
            "[STT API] Temporary file created:",
            audio_path
        )


        # -----------------------------------
        # 8.4. CONVERT AUDIO INTO TEXT
        # -----------------------------------

        print(
            "[STT API] Starting transcription...",
            flush=True
        )

        transcription = transcribe_audio(
            audio_path
        )

        print(
            "[STT API] Transcription:",
            transcription
        )


        # -----------------------------------
        # 8.5. CALCULATE STT LATENCY
        # -----------------------------------

        latency = time.perf_counter() - start_time

        print(
            "[STT API] Latency:",
            round(latency, 3),
            "seconds"
        )


        # -----------------------------------
        # 8.6. RETURN TRANSCRIPTION
        # -----------------------------------

        return {
            "text": transcription,
            "latency": round(latency, 3)
        }


    # -----------------------------------
    # 8.7. HANDLE HTTP ERRORS
    # -----------------------------------

    except HTTPException:

        raise


    # -----------------------------------
    # 8.8. HANDLE TRANSCRIPTION ERRORS
    # -----------------------------------

    except Exception as error:

        print("[STT API ERROR]", error)

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


    # -----------------------------------
    # 8.9. CLEAN UP TEMPORARY AUDIO
    # -----------------------------------

    finally:

        file.file.close()

        if audio_path is not None:

            Path(audio_path).unlink(
                missing_ok=True
            )


# ===================================
# 9. TEXT-TO-SPEECH API ENDPOINT
# ===================================

@app.post(
    "/synthesize",
    response_class=Response,
    responses={
        200: {
            "content": {
                "audio/wav": {}
            },
            "description": "Generated WAV audio"
        }
    }
)
def synthesize(request: TTSRequest):

    # Record the starting time.

    start_time = time.perf_counter()

    # Store the temporary audio file path.

    audio_path = None

    # Extract the text from the request.

    text = request.text.strip()


    # -----------------------------------
    # 9.1. VALIDATE INPUT TEXT
    # -----------------------------------

    if not text:

        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty"
        )

    # Limit excessively long requests.

    if len(text) > 2000:

        raise HTTPException(
            status_code=400,
            detail="Text is too long"
        )

    try:

        print(
            "[TTS API] Received text:",
            text,
            flush=True
        )


        # -----------------------------------
        # 9.2. CREATE TEMPORARY AUDIO FILE
        # -----------------------------------

        with tempfile.NamedTemporaryFile(

            suffix=".wav",

            delete=False

        ) as temporary_file:

            audio_path = temporary_file.name

        print(
            "[TTS API] Temporary file created:",
            audio_path,
            flush=True
        )


        # -----------------------------------
        # 9.3. GENERATE SPEECH USING PIPER
        # -----------------------------------

        print(
            "[TTS API] Starting Piper TTS...",
            flush=True
        )

        generate_speech(
            text,
            audio_path
        )

        print(
            "[TTS API] Piper TTS completed.",
            flush=True
        )


        # -----------------------------------
        # 9.4. READ GENERATED AUDIO
        # -----------------------------------

        audio_data = Path(audio_path).read_bytes()

        # Verify that audio data was generated.

        if len(audio_data) <= 44:

            raise RuntimeError(
                "Generated audio contains no usable WAV data"
            )

        print(
            "[TTS API] Audio size:",
            len(audio_data),
            "bytes"
        )


        # -----------------------------------
        # 9.5. CALCULATE TTS LATENCY
        # -----------------------------------

        latency = time.perf_counter() - start_time

        print(
            "[TTS API] Latency:",
            round(latency, 3),
            "seconds"
        )


        # -----------------------------------
        # 9.6. RETURN WAV AUDIO RESPONSE
        # -----------------------------------

        return Response(

            content=audio_data,

            media_type="audio/wav",

            headers={
                "X-TTS-Latency": str(
                    round(latency, 3)
                )
            }
        )


    # -----------------------------------
    # 9.7. HANDLE TTS ERRORS
    # -----------------------------------

    except HTTPException:

        raise

    except Exception as error:

        print("[TTS API ERROR]", error)

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


    # -----------------------------------
    # 9.8. CLEAN UP TEMPORARY AUDIO
    # -----------------------------------

    finally:

        if audio_path is not None:

            Path(audio_path).unlink(
                missing_ok=True
            )
