import os
import re
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from asr import return_transcription
from correction import correction
from rag import rag_respond
from ticket import generate_ticket
from tts import get_audio_base64
import logger

# ── Path setup ───────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

load_dotenv(dotenv_path=ROOT_DIR / ".env")
load_dotenv(find_dotenv(usecwd=False))

# ── Per-session state (single-user demo) ─────────────────────────
# conversation_history: list of {"role": "user"|"assistant", "content": "..."}
# attempt_count: how many troubleshoot responses have been given this session.
#                Hard limit is MAX_ATTEMPTS — once reached, the next response
#                is always "escalate" regardless of what the LLM returns.
# ── Tier 2 rule-based pre-check ──────────────────────────────────
# These patterns fire BEFORE the LLM and guarantee immediate escalation
# regardless of what the RAG pipeline would otherwise decide.
_TIER2_PATTERNS = [
    # Multiple users affected
    r'\b(everyone|entire\s+team|whole\s+(team|office|company|department|floor))\b',
    r'\ball\s+(of\s+us|users?|staff|employees?|colleagues?)\b',
    r'\b(no\s+one|nobody|none\s+of\s+us)\b.{0,50}\b(can|able\s+to)\b',
    r'\b(multiple|several|many)\s+users?\b.{0,40}\b(affected|same\s+issue|experiencing)\b',
    # Critical infrastructure
    r'\b(production|prod)\b.{0,25}\b(down|offline|unreachable|not\s+respond)\b',
    r'\b(server|database|db|sql|domain\s+controller)\b.{0,25}\b(down|crash|offline|unreachable)\b',
    r'\bactive\s+directory\b.{0,25}\b(down|offline|completely|unavailable)\b',
    # Security incidents
    r'\b(ransomware|malware|breach|hacked|phishing\s+attack|cyber\s+attack|virus\s+spread)\b',
]
_TIER2_RE = re.compile('|'.join(_TIER2_PATTERNS), re.IGNORECASE)

def _is_tier2(text: str) -> bool:
    return bool(_TIER2_RE.search(text))

MAX_ATTEMPTS = 3       # hard escalation after this many troubleshoot responses
MAX_CLARIFY  = 3       # after this many consecutive unintelligible inputs, give up gracefully
conversation_history: list[dict] = []
attempt_count: int       = 0     # troubleshoot responses given this session
clarify_count: int       = 0     # consecutive unintelligible/clarify turns
pending_correction: str | None = None   # corrected transcript awaiting user confirmation

# Words that count as "yes, that's right" when confirming a correction
_CONFIRM_WORDS = {"yes", "yeah", "yep", "yup", "correct", "right", "sure", "exactly",
                  "affirmative", "that's right", "thats right", "that is right"}

# ── App init ─────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Static routes ─────────────────────────────────────────────────
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/")
async def serve_home():
    return FileResponse(FRONTEND_DIR / "index.html")

app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

# ── Voice ID helper ───────────────────────────────────────────────
def resolve_voice_id(voice_gender: str) -> str:
    female = os.getenv("ELEVENLABS_VOICE_ID_FEMALE")
    male   = os.getenv("ELEVENLABS_VOICE_ID_MALE")
    if voice_gender == "female":
        return female or male
    return male or female

# ── /speak — frontend TTS requests ───────────────────────────────
class SpeakRequest(BaseModel):
    text: str
    voice_id: str

@app.post("/speak")
async def speak_handler(request: SpeakRequest):
    v_id = resolve_voice_id(request.voice_id)
    audio_data = await get_audio_base64(request.text, v_id)
    return {"audio": audio_data if audio_data else ""}

# ── /process — main RAG pipeline ─────────────────────────────────
@app.post("/process")
async def process_call(
    file: UploadFile = File(...),
    voice_id: str = Form("male")
):
    global conversation_history, attempt_count, clarify_count, pending_correction
    tmp_path = None
    try:
        # 1. Save audio to temp file
        suffix = Path(file.filename).suffix or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # ── Request header ────────────────────────────────────────
        logger.section(f"NEW REQUEST  │  attempt {attempt_count}/{MAX_ATTEMPTS}  │  clarify streak {clarify_count}/{MAX_CLARIFY}")

        # 2. ASR
        raw_transcript = return_transcription(tmp_path)
        if not raw_transcript or not raw_transcript.strip():
            return {
                "error": "no_audio",
                "bot_message": "Sorry, I didn't catch that — could you try again?",
                "audio": ""
            }

        # 3. Fuzzy + LLM correction
        correction_result = correction(raw_transcript)
        corrected    = correction_result.get("corrected_transcript", raw_transcript)
        confidence   = correction_result.get("confidence", "low")
        corrections  = correction_result.get("corrections", [])

        # 3a. Pending-confirmation check ──────────────────────────────
        # If the previous turn asked the user to confirm a correction, resolve it now.
        if pending_correction is not None:
            simple = corrected.lower().strip().rstrip(".,!")
            if any(w in simple.split() for w in _CONFIRM_WORDS):
                logger.process_gate("CORRECTION CONFIRMED", f"applying → '{pending_correction}'")
                corrected   = pending_correction
                confidence  = "high"
                corrections = []
            else:
                logger.process_gate("CORRECTION REJECTED", "user rephrased — using new input directly")
            pending_correction = None

        # 3b. Uncertain-correction gate ───────────────────────────────
        # When the LLM changed the transcript but isn't confident, ask before acting.
        elif confidence in ("medium", "low") and corrections and corrected != raw_transcript:
            corrected_terms = [c["corrected"] for c in corrections]
            terms_str = " and ".join(f'"{t}"' for t in corrected_terms)
            bot_message = (
                f"Sorry, I had a little trouble hearing that clearly. "
                f"Did you say {terms_str}? Just confirm and I'll get right on it, "
                f"or go ahead and rephrase if I got it wrong."
            )
            pending_correction = corrected
            action = "clarify"
            intent = "other"

            conversation_history.append({"role": "user",      "content": raw_transcript})
            conversation_history.append({"role": "assistant", "content": bot_message})
            logger.process_gate("AWAITING CONFIRMATION", f"uncertain correction — asking user to confirm {terms_str}")
            logger.bot_reply(bot_message)
            audio_b64 = await get_audio_base64(bot_message, resolve_voice_id(voice_id))
            return {
                "corrected_transcript": raw_transcript,
                "intent": intent,
                "action": action,
                "bot_message": bot_message,
                "audio": audio_b64 if audio_b64 else "",
                "ticket": None
            }

        # 4a. Pre-flight gibberish check
        words        = corrected.split()
        alpha_ratio  = sum(c.isalpha() for c in corrected) / max(len(corrected), 1)
        is_gibberish = (confidence == "low" and len(words) < 3) or alpha_ratio < 0.5

        if is_gibberish:
            clarify_count += 1
            logger.process_clarify(clarify_count, MAX_CLARIFY)

        # 4b. Tier 2 rule-based gate — fires before LLM, cannot be overridden
        if not is_gibberish and _is_tier2(corrected):
            logger.process_gate("TIER 2 DETECTED", f"rule-based match in: '{corrected[:60]}'")
            bot_message = (
                "This sounds like it's affecting multiple users or a critical system — "
                "that's a Tier 2 issue that needs immediate attention from our infrastructure "
                "team. I'm creating a high-priority ticket right now and a specialist will "
                "be in touch with you shortly."
            )
            action = "escalate"
            intent = "other"

        # 4c. Clarify wall
        elif clarify_count >= MAX_CLARIFY:
            clarify_count = 0
            bot_message = (
                "I'm really sorry — I've had trouble understanding your last few messages. "
                "If you're having difficulty with the voice interface, please use the "
                "'Live Agent' button to speak with a human representative directly."
            )
            action = "clarify_wall"
            intent = "other"
            logger.process_gate("CLARIFY WALL", f"streak reached {MAX_CLARIFY}")

        # 4e. Attempt limit reached — one final LLM exchange before hard escalation.
        #     The LLM may complete any in-progress step (e.g. explain how to uninstall)
        #     but cannot propose a brand-new troubleshooting approach.
        #     If it still returns "troubleshoot", we push attempt_count over the limit
        #     so the NEXT request hard-escalates unconditionally.
        elif attempt_count >= MAX_ATTEMPTS:
            logger.process_gate("FINAL EXCHANGE", f"limit {MAX_ATTEMPTS} reached — LLM gets one wrap-up turn")
            rag_result  = rag_respond(corrected, conversation_history,
                                      attempt=attempt_count + 1, is_final=True)
            bot_message = rag_result["message"]
            action      = rag_result["action"]
            intent      = rag_result.get("intent", "other")

            if action == "troubleshoot":
                # LLM chose to complete the current step rather than escalate.
                # Push the counter past the limit so the very next request
                # hard-escalates with no further LLM call.
                attempt_count += 1
                logger.process_attempt(attempt_count, MAX_ATTEMPTS)
            clarify_count = 0

        else:
            # 4d. Normal RAG path
            rag_result  = rag_respond(corrected, conversation_history, attempt=attempt_count + 1)
            bot_message = rag_result["message"]
            action      = rag_result["action"]
            intent      = rag_result.get("intent", "other")

            if action == "clarify":
                clarify_count += 1
                logger.process_clarify(clarify_count, MAX_CLARIFY)
            else:
                clarify_count = 0

            if action == "troubleshoot":
                attempt_count += 1
                logger.process_attempt(attempt_count, MAX_ATTEMPTS)

        # 5. Update conversation history
        conversation_history.append({"role": "user",      "content": corrected})
        conversation_history.append({"role": "assistant", "content": bot_message})

        # 6. TTS
        logger.bot_reply(bot_message)
        audio_b64 = await get_audio_base64(bot_message, resolve_voice_id(voice_id))

        # 7. Generate ticket on escalate or close; clear state on any session end
        ticket = None
        if action in ("escalate", "close"):
            logger.ticket_created(action, intent)
            session = {
                "caller_id": "Unknown",
                "tier": "2" if action == "escalate" else "1",
                "intent": intent,
                "raw_transcript": raw_transcript,
                "corrected_transcript": corrected,
                "corrections": correction_result.get("corrections", []),
                "steps_taken": [
                    m["content"] for m in conversation_history
                    if m["role"] == "assistant"
                ],
                "outcome": action,
                "escalation_reason": (
                    f"Hard limit reached after {MAX_ATTEMPTS} attempts"
                    if attempt_count >= MAX_ATTEMPTS
                    else f"RAG pipeline — action: {action}, intent: {intent}"
                )
            }
            ticket = generate_ticket(session)
            conversation_history = []
            attempt_count  = 0
            clarify_count  = 0

        return {
            "corrected_transcript": corrected,
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

# ── /asr — transcript only (kept for backwards compatibility) ─────
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

# ── /reset — clear server-side conversation history ───────────────
@app.post("/reset")
async def reset_session():
    global conversation_history, attempt_count, clarify_count, pending_correction
    conversation_history = []
    attempt_count      = 0
    clarify_count      = 0
    pending_correction = None
    print("[Session] Conversation history and all counters cleared.")
    return {"status": "ok"}

# ── Entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
