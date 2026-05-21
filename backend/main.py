import os
import json
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from asr import return_transcription
from correction import correction
from classify import classify
from routing import route
from ticket import generate_ticket
from tts import get_audio_base64

# ── Path setup ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

load_dotenv(dotenv_path=ROOT_DIR / ".env")   # normal project layout
load_dotenv(find_dotenv(usecwd=False))        # fallback: walk up from this file (covers worktree)

# ── App init ─────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Static routes ─────────────────────────────────────────────
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/")
async def serve_home():
    return FileResponse(FRONTEND_DIR / "index.html")

app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

# ── /speak endpoint (frontend TTS requests) ───────────────────
class SpeakRequest(BaseModel):
    text: str
    voice_id: str

def resolve_voice_id(voice_gender: str) -> str:
    female = os.getenv("ELEVENLABS_VOICE_ID_FEMALE")
    male = os.getenv("ELEVENLABS_VOICE_ID_MALE")
    if voice_gender == "female":
        return female or male
    return male or female

@app.post("/speak")
async def speak_handler(request: SpeakRequest):
    v_id = resolve_voice_id(request.voice_id)
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
        if not raw_transcript:
            return {"error": "no_audio", "bot_message": "Sorry, I didn't catch that. Could you try again?", "audio": ""}

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
        audio_b64 = await get_audio_base64(bot_message, resolve_voice_id(voice_id))

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

# ── /asr endpoint (transcript only, used during troubleshoot follow-ups) ─
@app.post("/asr")
async def asr_only(file: UploadFile = File(...)):
    tmp_path = None
    try:
        suffix = Path(file.filename).suffix or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        transcript = return_transcription(tmp_path)
        return {"transcript": transcript or ""}
    except Exception as e:
        print(f"[asr_only] Error: {e}")
        return {"transcript": ""}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── /close endpoint (user confirmed issue resolved) ───────────
@app.post("/close")
async def close_session(voice_id: str = Form("female")):
    message = "Excellent! I am glad we were able to resolve the issue. Thank you for contacting IT support. Have a wonderful day!"
    audio_b64 = await get_audio_base64(message, resolve_voice_id(voice_id))
    session = {
        "caller_id": "Unknown",
        "tier": "1",
        "intent": "resolved",
        "raw_transcript": "",
        "corrected_transcript": "",
        "corrections": [],
        "steps_taken": [],
        "outcome": "close",
        "escalation_reason": None
    }
    ticket = generate_ticket(session)
    return {"bot_message": message, "audio": audio_b64 or "", "action": "close", "ticket": ticket}


# ── /step endpoint (fetch next troubleshooting step by intent) ─
@app.post("/step")
async def get_step(intent: str = Form("other"), step: int = Form(0), voice_id: str = Form("female")):
    with open(BASE_DIR / "kb.json", encoding="utf-8") as f:
        kb_data = json.load(f)
    topic = intent.lower() if intent.lower() in kb_data else "other"
    steps = kb_data.get(topic, kb_data.get("other", []))
    if step >= len(steps):
        message = "We have gone through all standard remote troubleshooting steps, but the issue persists. I am creating a high-priority ticket for our desktop support team."
        action = "escalate"
    else:
        message = steps[step]
        action = "troubleshoot"
    audio_b64 = await get_audio_base64(message, resolve_voice_id(voice_id))
    return {"bot_message": message, "audio": audio_b64 or "", "action": action}


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)