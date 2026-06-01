# IT Helpdesk Voice Bot

An AI-powered voice assistant that handles Tier 1 IT support calls autonomously - triaging issues, walking users through troubleshooting steps, and escalating to human agents when necessary. Built with a push-to-talk interface, real-time ASR correction, RAG-grounded responses, and auto-generated PDF support tickets.

---

## Features

- **Push-to-talk voice interface** - hold to speak, release to process
- **Real-time waveform visualizer** - mic audio rendered live inside the orb during recording
- **Whisper ASR** - local, on-device speech-to-text
- **Two-stage ASR correction** - fuzzy matching + LLM contextual correction with a confirmation gate for uncertain corrections
- **RAG pipeline** - ChromaDB + Sentence-Transformers retrieves relevant IT knowledge before each LLM response
- **Structured escalation logic** - Tier 2 rule-based detection, clarify wall, attempt limit, sub-question awareness
- **PDF ticket generation** - auto-generated on every session end with LLM-distilled steps and outcome
- **Voice & theme toggles** - male/female TTS voice, dark/light mode
- **Live agent transfer** - manual escalation button

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript (Web Audio API, MediaRecorder, Lottie) |
| Backend | FastAPI (Python 3.11) |
| Speech-to-Text | OpenAI Whisper (tiny model) - runs locally |
| ASR Correction – Fuzzy | RapidFuzz |
| ASR Correction – LLM | Groq API (LLaMA 3.3 70B) |
| Vector Database | ChromaDB + Sentence-Transformers (all-MiniLM-L6-v2) |
| LLM / RAG Generation | Groq API (LLaMA 3.3 70B) |
| Text-to-Speech | ElevenLabs API |
| PDF Generation | ReportLab |

---

## Project Structure

```
IT-Helpdesk-Voice-Bot/
├── backend/
│   ├── main.py              # FastAPI app, session state, escalation gates
│   ├── asr.py               # Whisper transcription + IT prompt
│   ├── correction.py        # Orchestrates fuzzy + LLM correction
│   ├── fuzzy_correction.py  # RapidFuzz word-level matching
│   ├── llm_correction.py    # Groq LLM sentence-level correction
│   ├── rag.py               # ChromaDB retrieval + Groq generation
│   ├── ticket.py            # ReportLab PDF ticket generator
│   ├── tts.py               # ElevenLabs TTS
│   ├── logger.py            # Structured console logging
│   ├── ingest.py            # One-time knowledge base ingestion script
│   ├── it_vocab.json        # 500+ IT terms (single source of truth)
│   └── knowledge/           # Source documents for RAG (8 .txt files)
├── frontend/
│   ├── index.html
│   ├── app.js               # Push-to-talk, waveform visualizer, chat UI
│   └── style.css
├── tickets/                 # Auto-generated PDF tickets (gitignored)
├── requirements.txt
└── .env                     # API keys (not committed)
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- A microphone

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID_MALE=your_male_voice_id
ELEVENLABS_VOICE_ID_FEMALE=your_female_voice_id
```

- **Groq API key** - free at https://console.groq.com
- **ElevenLabs API key** - https://elevenlabs.io (free tier available)
- Voice IDs are found in your ElevenLabs voice library

### 4. Build the knowledge base (first run only)

```bash
cd backend
python ingest.py
```

This chunks and embeds the 8 knowledge documents into ChromaDB. Only needs to run once.

### 5. Start the server

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 6. Open the app

Navigate to http://localhost:8000 in your browser.

---

## Usage

1. **Click the orb** - the bot greets you with Alex's welcome message
2. **Hold the orb** to speak, **release** to send
3. The waveform visualizer shows your mic input in real time
4. The bot responds via voice and text chat
5. Use the theme button to toggle dark/light mode
6. Use the voice icon to switch between male and female TTS voices
7. Use the reset button to start a new session
8. Use **Live Agent** to manually request a human transfer

PDF tickets are automatically saved to the `/tickets/` folder at the end of each session.

---

## Escalation Behaviour

| Trigger | Response |
|---|---|
| Multi-user outage ("nobody can connect", "entire team affected") | Immediate Tier 2 escalation |
| Critical infrastructure down (server, database, domain controller) | Immediate Tier 2 escalation |
| Security incident (ransomware, breach, malware) | Immediate Tier 2 escalation |
| Hard deadline + system failure ("presentation in 20 minutes, computer won't start") | Immediate urgent escalation |
| 3 failed troubleshooting attempts | Escalation with LLM wrap-up (sub-questions still answered) |
| 3 consecutive unintelligible inputs | Clarify wall - suggests Live Agent |
| 20 total turns | Session cap - graceful escalation |

