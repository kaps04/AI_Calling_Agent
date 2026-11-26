
// ===================================
// 1. IMPORT LIBRARIES
// ===================================

import { useState, useEffect, useRef } from "react";

import "./App.css";


// ===================================
// 2. DEFINE API CONFIGURATION
// ===================================

const API_URL = "http://127.0.0.1:8000";


// ===================================
// 3. DEFINE MAIN APPLICATION
// ===================================

function App() {

    // Customer text input.

    const [message, setMessage] = useState("");

    // Conversation history.

    const [messages, setMessages] = useState([
        {
            role: "agent",
            text: "Hello! How can I help you today?"
        }
    ]);

    // Conversation session ID.

    const [sessionId, setSessionId] = useState(null);

    // Detected customer intent.

    const [intent, setIntent] = useState("-");

    // Latency measurements.

    const [latency, setLatency] = useState(0);

    const [sttLatency, setSttLatency] = useState(0);

    const [ttsLatency, setTtsLatency] = useState(0);

    // Application status.

    const [loading, setLoading] = useState(false);

    const [backendOnline, setBackendOnline] = useState(false);

    const [error, setError] = useState("");

    // Voice recording status.

    const [recording, setRecording] = useState(false);

    const [voiceStatus, setVoiceStatus] = useState("Ready");

    // Enable spoken AI responses.

    const [voiceEnabled, setVoiceEnabled] = useState(true);


    // ===================================
    // 4. DEFINE REFERENCES
    // ===================================

    // Automatic conversation scrolling.

    const messagesEndRef = useRef(null);

    // Store the browser audio recorder.

    const mediaRecorderRef = useRef(null);

    // Store captured audio chunks.

    const audioChunksRef = useRef([]);

    // Store the microphone stream.

    const streamRef = useRef(null);

    // Store the currently playing audio.

    const audioRef = useRef(null);

    // Store the temporary browser audio URL.

    const audioUrlRef = useRef(null);

    // Prevent overlapping operations.

    const busyRef = useRef(false);

    // Prevent recording callbacks after unmount.

    const activeRef = useRef(true);


    // ===================================
    // 5. CHECK BACKEND CONNECTION
    // ===================================

    useEffect(() => {

        async function checkBackend() {

            try {

                const response = await fetch(
                    `${API_URL}/health`
                );

                setBackendOnline(response.ok);

            } catch {

                setBackendOnline(false);

            }
        }

        checkBackend();

        const interval = setInterval(
            checkBackend,
            5000
        );

        return () => clearInterval(interval);

    }, []);


    // ===================================
// 6. AUTOMATIC CONVERSATION SCROLLING
// ===================================

useEffect(() => {

    // Locate the conversation container.

    const container =
        messagesEndRef.current?.parentElement;

    // Scroll only inside the conversation.

    if (container) {

        container.scrollTo({

            top: container.scrollHeight,

            behavior: "smooth"

        });

    }

}, [messages, loading]);

    // ===================================
    // 8. HANDLE API RESPONSES
    // ===================================

    async function checkResponse(response) {

        if (!response.ok) {

            const details = await response.text();

            throw new Error(
                `HTTP ${response.status}: ${details}`
            );

        }

        return response;
    }


    // ===================================
    // 9. GENERATE AND PLAY AI SPEECH
    // ===================================

    async function speakResponse(text) {

        setVoiceStatus("Generating speech...");

        // Send the AI response to Piper TTS.

        const response = await fetch(
            `${API_URL}/synthesize`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    text: text
                })
            }
        );

        await checkResponse(response);

        // Read the TTS latency header.

        const measuredLatency = Number(
            response.headers.get("X-TTS-Latency")
        );

        setTtsLatency(
            Number.isFinite(measuredLatency)
                ? measuredLatency
                : 0
        );

        // Convert the HTTP response into audio data.

        const audioBlob = await response.blob();

        if (!activeRef.current) return;

        // Release the previous audio URL.

        if (audioUrlRef.current) {

            URL.revokeObjectURL(audioUrlRef.current);

        }

        // Create a browser-accessible audio URL.

        const audioUrl = URL.createObjectURL(audioBlob);

        audioUrlRef.current = audioUrl;

        // Create the browser audio player.

        const audio = new Audio(audioUrl);

        audioRef.current = audio;

        setVoiceStatus("Speaking...");

        // Wait until audio playback is completed.

        try {

            await new Promise((resolve, reject) => {

                audio.onended = resolve;

                audio.onerror = () => reject(
                    new Error("Audio playback failed")
                );

                audio.play().catch(reject);

            });

        } finally {

            URL.revokeObjectURL(audioUrl);

            audioUrlRef.current = null;

        }

        setVoiceStatus("Ready");
    }


    // ===================================
    // 10. SEND CUSTOMER MESSAGE TO FASTAPI
    // ===================================

    async function processMessage(
        customerMessage,
        source = "text"
    ) {

        // Reject empty messages.

        if (!customerMessage.trim()) return;

        // Add the customer message to the conversation.

        setMessages(previous => [
            ...previous,
            {
                role: "customer",
                text: customerMessage,
                source: source
            }
        ]);

        setVoiceStatus("Thinking...");

        // Send customer message to the existing chatbot.

        const response = await fetch(
            `${API_URL}/chat`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: customerMessage,
                    session_id: sessionId
                })
            }
        );

        await checkResponse(response);

        const result = await response.json();

        // Update conversation memory.

        setSessionId(result.session_id);

        // Update intent and latency.

        setIntent(result.intent);

        setLatency(result.latency);

        // Add the AI response to the conversation.

        setMessages(previous => [
            ...previous,
            {
                role: "agent",
                text: result.response
            }
        ]);

        // Speak the AI response if enabled.

        if (voiceEnabled) {

            await speakResponse(result.response);

        }
    }


    // ===================================
    // 11. HANDLE TEXT MESSAGE
    // ===================================

    async function sendMessage(event) {

        event.preventDefault();

        const customerMessage = message.trim();

        if (
            !customerMessage ||
            busyRef.current ||
            recording ||
            !backendOnline
        ) {

            return;

        }

        busyRef.current = true;

        setLoading(true);

        setError("");

        setMessage("");

        try {

            await processMessage(
                customerMessage,
                "text"
            );

        } catch (error) {

            console.error("[CHAT ERROR]", error);

            setError(error.message);

        } finally {

            busyRef.current = false;

            setLoading(false);

            setVoiceStatus("Ready");

        }
    }


    // ===================================
    // 12. CONVERT RECORDED AUDIO INTO TEXT
    // ===================================

    async function transcribeRecording(
        audioBlob,
        mimeType
    ) {

        setVoiceStatus("Transcribing...");

        // Select the appropriate file extension.

        let extension = "webm";

        if (mimeType.includes("mp4")) {

            extension = "mp4";

        } else if (mimeType.includes("ogg")) {

            extension = "ogg";

        } else if (mimeType.includes("wav")) {

            extension = "wav";

        }

        // Create multipart form data.

        const formData = new FormData();

        formData.append(
            "file",
            audioBlob,
            `customer.${extension}`
        );

        // Upload audio to Faster-Whisper.

        const response = await fetch(
            `${API_URL}/transcribe`,
            {
                method: "POST",

                body: formData
            }
        );

        await checkResponse(response);

        const result = await response.json();

        // Update transcription latency.

        setSttLatency(result.latency);

        console.log(
            "[STT]",
            result.text
        );

        return result.text;
    }


    // ===================================
    // 13. START MICROPHONE RECORDING
    // ===================================

    async function startRecording() {

        if (
            busyRef.current ||
            recording ||
            !backendOnline
        ) {

            return;

        }

        busyRef.current = true;

        setLoading(true);

        setError("");

        try {

            setVoiceStatus("Requesting microphone...");

            // Request browser microphone permission.

            const stream =
                await navigator.mediaDevices.getUserMedia({
                    audio: true
                });

            if (!activeRef.current) {

                stream.getTracks().forEach(
                    track => track.stop()
                );

                return;
            }

            streamRef.current = stream;

            // Select a supported audio format.

            const supportedTypes = [
                "audio/webm;codecs=opus",
                "audio/webm",
                "audio/mp4",
                "audio/ogg"
            ];

            const mimeType = supportedTypes.find(
                type => MediaRecorder.isTypeSupported(type)
            );

            // Create the browser audio recorder.

            const recorder = mimeType

                ? new MediaRecorder(
                    stream,
                    { mimeType: mimeType }
                )

                : new MediaRecorder(stream);

            mediaRecorderRef.current = recorder;

            // Clear previously recorded audio.

            audioChunksRef.current = [];


            // -----------------------------------
            // COLLECT AUDIO CHUNKS
            // -----------------------------------

            recorder.ondataavailable = event => {

                if (event.data.size > 0) {

                    audioChunksRef.current.push(
                        event.data
                    );

                }
            };


            // -----------------------------------
            // PROCESS AUDIO AFTER RECORDING
            // -----------------------------------

            recorder.onstop = async () => {

                // Release the microphone.

                stream.getTracks().forEach(
                    track => track.stop()
                );

                streamRef.current = null;

                if (!activeRef.current) return;

                setRecording(false);

                setLoading(true);

                try {

                    // Combine the recorded audio chunks.

                    const audioType =
                        recorder.mimeType ||
                        mimeType ||
                        "audio/webm";

                    const audioBlob = new Blob(

                        audioChunksRef.current,

                        {
                            type: audioType
                        }
                    );

                    if (audioBlob.size === 0) {

                        throw new Error(
                            "No audio was recorded."
                        );

                    }

                    // Convert customer audio into text.

                    const transcription =
                        await transcribeRecording(
                            audioBlob,
                            audioType
                        );

                    if (!transcription.trim()) {

                        setVoiceStatus("No speech detected");

                        return;

                    }

                    // Send recognized text to the AI agent.

                    await processMessage(
                        transcription,
                        "voice"
                    );

                } catch (error) {

                    console.error(
                        "[VOICE ERROR]",
                        error
                    );

                    setError(error.message);

                } finally {

                    busyRef.current = false;

                    setLoading(false);

                    setVoiceStatus("Ready");

                }
            };


            // -----------------------------------
            // HANDLE RECORDING ERRORS
            // -----------------------------------

            recorder.onerror = () => {

                stream.getTracks().forEach(
                    track => track.stop()
                );

                recorder.onstop = null;

                streamRef.current = null;

                busyRef.current = false;

                setRecording(false);

                setLoading(false);

                setVoiceStatus("Ready");

                setError("Microphone recording failed.");

            };


            // -----------------------------------
            // BEGIN RECORDING
            // -----------------------------------

            recorder.start();

            setRecording(true);

            setLoading(false);

            setVoiceStatus("Recording...");

            console.log("[MIC] Recording started");

        } catch (error) {

            streamRef.current?.getTracks().forEach(
                track => track.stop()
            );

            streamRef.current = null;

            busyRef.current = false;

            setRecording(false);

            setLoading(false);

            setVoiceStatus("Ready");

            setError(error.message);

        }
    }


    // ===================================
    // 14. STOP MICROPHONE RECORDING
    // ===================================

    function stopRecording() {

        const recorder = mediaRecorderRef.current;

        if (
            recorder &&
            recorder.state === "recording"
        ) {

            setLoading(true);

            setVoiceStatus("Processing audio...");

            recorder.stop();

            console.log("[MIC] Recording stopped");

        }
    }


    // ===================================
    // 15. START NEW CONVERSATION
    // ===================================

    function newConversation() {

        if (busyRef.current || recording) return;

        setSessionId(null);

        setIntent("-");

        setLatency(0);

        setSttLatency(0);

        setTtsLatency(0);

        setMessage("");

        setError("");

        setVoiceStatus("Ready");

        setMessages([
            {
                role: "agent",
                text: "Hello! How can I help you today?"
            }
        ]);
    }


    // ===================================
    // 16. BUILD USER INTERFACE
    // ===================================

    return (

        <div className="dashboard">


            {/* HEADER */}

            <header className="header">

                <div>

                    <h1>AI Business Calling Agent</h1>

                    <p>
                        Intelligent Customer Support System
                    </p>

                </div>

                <span
                    className={
                        backendOnline
                            ? "status online"
                            : "status offline"
                    }
                >

                    {backendOnline
                        ? "Backend Online"
                        : "Backend Offline"}

                </span>

            </header>


            {/* LATENCY MONITORING */}

            <section className="metrics">

                <div className="metric-card">

                    <p>STT Latency</p>

                    <h2>{sttLatency.toFixed(3)} s</h2>

                </div>

                <div className="metric-card">

                    <p>API Latency</p>

                    <h2>{latency.toFixed(3)} s</h2>

                </div>

                <div className="metric-card">

                    <p>TTS Latency</p>

                    <h2>{ttsLatency.toFixed(3)} s</h2>

                </div>

            </section>


            {/* VOICE CONTROL PANEL */}

            <section className="voice-panel">

                <div
                    className={
                        recording
                            ? "microphone-icon recording"
                            : "microphone-icon"
                    }
                >

                    🎙

                </div>

                <h2>Voice Conversation</h2>

                <p className="voice-status">

                    {voiceStatus}

                </p>

                <p className="detected-intent">

                    Detected Intent:{" "}

                    {intent.replaceAll("_", " ")}

                </p>


                {/* RECORDING CONTROLS */}

                <div className="voice-controls">

                    <button

                        className="start-recording"

                        onClick={startRecording}

                        disabled={
                            recording ||
                            loading ||
                            !backendOnline
                        }

                    >

                        Start Recording

                    </button>

                    <button

                        className="stop-recording"

                        onClick={stopRecording}

                        disabled={!recording || loading}

                    >

                        Stop Recording

                    </button>

                </div>


                {/* VOICE RESPONSE OPTION */}

                <label className="voice-option">

                    <input

                        type="checkbox"

                        checked={voiceEnabled}

                        disabled={loading || recording}

                        onChange={event =>
                            setVoiceEnabled(
                                event.target.checked
                            )
                        }

                    />

                    Enable spoken responses

                </label>

            </section>


            {/* CONVERSATION INTERFACE */}

            <section className="chat-container">

                <div className="chat-header">

                    <h2>Conversation</h2>

                    <button

                        onClick={newConversation}

                        disabled={loading || recording}

                    >

                        New Conversation

                    </button>

                </div>


                {/* DISPLAY CONVERSATION */}

                <div className="messages">

                    {messages.map((item, index) => (

                        <div

                            key={index}

                            className={`message ${item.role}`}

                        >

                            <span className="message-role">

                                {item.role === "agent"

                                    ? "AI Agent"

                                    : item.source === "voice"

                                        ? "Customer · Voice"

                                        : "Customer"}

                            </span>

                            <p>{item.text}</p>

                        </div>

                    ))}

                    {loading && (

                        <div className="message agent">

                            {voiceStatus}

                        </div>

                    )}

                    <div ref={messagesEndRef} />

                </div>


                {/* DISPLAY ERRORS */}

                {error && (

                    <p className="error">

                        {error}

                    </p>

                )}


                {/* TEXT MESSAGE INPUT */}

                <form

                    className="input-container"

                    onSubmit={sendMessage}

                >

                    <input

                        type="text"

                        placeholder="Enter your message..."

                        value={message}

                        onChange={event =>
                            setMessage(event.target.value)
                        }

                        disabled={loading || recording}

                    />

                    <button

                        type="submit"

                        disabled={
                            loading ||
                            recording ||
                            !backendOnline
                        }

                    >

                        {loading
                            ? "Processing..."
                            : "Send"}

                    </button>

                </form>

            </section>


            {/* SESSION INFORMATION */}

            <footer>

                Session: {sessionId || "Not started"}

                <p>

                    Qwen | LangGraph | FastAPI |
                    Whisper | Piper

                </p>

            </footer>

        </div>

    );
}


// ===================================
// 17. EXPORT APPLICATION
// ===================================

export default App;
