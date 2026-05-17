import os
import json
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from asr import return_transcription
from correction import correction
from classify import classify
# from routing import route          # Ido — route() must exist before this works
from ticket import generate_ticket
from tts import get_audio_base64

# ── Path setup ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

load_dotenv(dotenv_path=ROOT_DIR / ".env")

# ── App init ─────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Static routes ─────────────────────────────────────────────
@app.get("/")
async def serve_home():
    return FileResponse(FRONTEND_DIR / "index.html")

app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

# ── /speak endpoint (frontend TTS requests) ───────────────────
class SpeakRequest(BaseModel):
    text: str
    voice_id: str

@app.post("/speak")
async def speak_handler(request: SpeakRequest):
    v_id = (
        os.getenv("ELEVENLABS_VOICE_ID_FEMALE")
        if request.voice_id == "female"
        else os.getenv("ELEVENLABS_VOICE_ID_MALE")
    )
    audio_data = await get_audio_base64(request.text, v_id)
    return {"audio": audio_data if audio_data else ""}

# ── /process endpoint (main pipeline) ────────────────────────
@app.post("/process")
async def process_call(
    file: UploadFile = File(...),
    step: int = Form(0),
    resolved: bool = Form(False),
    voice_id: str = Form("female")
):
    tmp_path = None
    try:
        # 1. Write audio to temp file (Whisper needs a file path)
        suffix = Path(file.filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # 2. ASR
        raw_transcript = return_transcription(tmp_path)

        # 3. ASR error correction (fuzzy + LLM, handled internally)
        correction_result = correction(raw_transcript)
        corrected_transcript = correction_result["corrected_transcript"]
        corrections_applied = correction_result["corrections"]

        # 4. Classification
        classification = classify(corrected_transcript)
        tier = classification["tier"]
        intent = classification["intent"]

        # 5. Routing (Ido) — requires routing.py with route() implemented
        route_result = route(tier=tier, intent=intent, step=step, resolved=resolved)
        action = route_result["action"]
        bot_message = route_result["message"]

        # 6. TTS
        v_id = (
            os.getenv("ELEVENLABS_VOICE_ID_FEMALE")
            if voice_id == "female"
            else os.getenv("ELEVENLABS_VOICE_ID_MALE")
        )
        audio_b64 = await get_audio_base64(bot_message, v_id)

        # 7. Build session + generate ticket on escalation/close
        session = {
            "caller_id": "Unknown",  # mocked — no auth system
            "tier": tier,
            "intent": intent,
            "raw_transcript": raw_transcript,
            "corrected_transcript": corrected_transcript,
            "corrections": corrections_applied,
            "steps_taken": [bot_message] if action == "troubleshoot" else [],
            "outcome": action,
            "escalation_reason": route_result.get("reason")
        }
        ticket = generate_ticket(session) if action in ("escalate", "close") else None

        # 8. Return
        return {
            "raw_transcript": raw_transcript,
            "corrected_transcript": corrected_transcript,
            "corrections": corrections_applied,
            "tier": tier,
            "intent": intent,
            "action": action,
            "bot_message": bot_message,
            "audio": audio_b64 if audio_b64 else "",
            "ticket": ticket
        }

    except Exception as e:
        print(f"[process_call] Error: {e}")
        return {"error": str(e)}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)