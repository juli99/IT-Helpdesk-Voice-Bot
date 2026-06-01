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
    # Time-critical emergency: hard deadline + complete system failure
    r'\b(presentation|meeting|demo|call|interview|class)\b.{0,60}\b(\d+\s+minutes?|few\s+minutes?|right\s+now|any\s+minute)\b',
    r'\b(\d+\s+minutes?|few\s+minutes?|right\s+now)\b.{0,60}\b(presentation|meeting|demo|call|interview)\b',
]
_TIER2_RE = re.compile('|'.join(_TIER2_PATTERNS), re.IGNORECASE)

# Subset of Tier 2 patterns that represent time-critical emergencies (not infra/multi-user)
_TIER2_URGENT_PATTERNS = [
    r'\b(presentation|meeting|demo|call|interview|class)\b.{0,60}\b(\d+\s+minutes?|few\s+minutes?|right\s+now|any\s+minute)\b',
    r'\b(\d+\s+minutes?|few\s+minutes?|right\s+now)\b.{0,60}\b(presentation|meeting|demo|call|interview)\b',
]
_TIER2_URGENT_RE = re.compile('|'.join(_TIER2_URGENT_PATTERNS), re.IGNORECASE)

def _is_tier2(text: str) -> bool:
    return bool(_TIER2_RE.search(text))

def _is_tier2_urgent(text: str) -> bool:
    """True when the Tier 2 trigger is a time-critical emergency (not infra/multi-user)."""
    return bool(_TIER2_URGENT_RE.search(text))

MAX_ATTEMPTS = 3       # hard escalation after this many troubleshoot responses
MAX_CLARIFY  = 3       # after this many consecutive unintelligible inputs, give up gracefully
MAX_TURNS    = 20      # absolute session cap — prevents endless clarification loops
conversation_history: list[dict] = []
attempt_count: int       = 0     # troubleshoot responses given this session
clarify_count: int       = 0     # consecutive unintelligible/clarify turns
total_turns:  int        = 0     # every bot response, regardless of action type
pending_correction: str | None = None   # corrected transcript awaiting user confirmation
troubleshoot_steps: list[str] = []      # only bot messages with action == "troubleshoot"
last_intent:       str  = "other"   # carried into the hard-escalate path (no LLM there)
tier2_escalation: bool  = False     # True only when the rule-based Tier 2 gate fires

# Words/phrases that count as "yes, that's right" when confirming a correction
_CONFIRM_WORDS = {"yes", "yeah", "yep", "yup", "correct", "right", "sure", "exactly",
                  "affirmative", "indeed", "absolutely", "confirmed", "did", "said",
                  "that's right", "thats right", "that is right", "i did", "that's it",
                  "thats it", "that's correct", "thats correct"}

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
    global conversation_history, attempt_count, clarify_count, pending_correction, troubleshoot_steps, last_intent, tier2_escalation, total_turns
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

        # 3a. Early Tier 2 check ──────────────────────────────────────
        # Run BEFORE the confirmation gate so a Tier 2 emergency is never delayed
        # by a "did you mean X?" turn. Check both the corrected text and the raw
        # transcript — a single misheard word ("sense"→"since") must not block escalation.
        _tier2_now = _is_tier2(corrected) or _is_tier2(raw_transcript)

        # 3b. Pending-confirmation check ──────────────────────────────
        # If the previous turn asked the user to confirm a correction, resolve it now.
        # Also check if the stored pending correction was itself a Tier 2 message —
        # if so, the confirmation answer is irrelevant; escalate immediately.
        if pending_correction is not None:
            if _is_tier2(pending_correction):
                # The original message was Tier 2 — escalate regardless of user reply
                logger.process_gate("TIER 2 IN PENDING", f"escalating stored correction: '{pending_correction[:60]}'")
                corrected        = pending_correction
                _tier2_now       = True
                tier2_escalation = True
                pending_correction = None
            else:
                simple = corrected.lower().strip().rstrip(".,!")
                # Check word-by-word AND substring (catches "I did say that", "that's it" etc.)
                confirmed = (
                    any(w in simple.split() for w in _CONFIRM_WORDS) or
                    any(phrase in simple for phrase in _CONFIRM_WORDS if len(phrase.split()) > 1)
                )
                if confirmed:
                    logger.process_gate("CORRECTION CONFIRMED", f"applying → '{pending_correction}'")
                    corrected   = pending_correction
                    confidence  = "high"
                    corrections = []
                else:
                    logger.process_gate("CORRECTION REJECTED", "user rephrased — using new input directly")
                pending_correction = None

        # 3c. Uncertain-correction gate ───────────────────────────────
        # When the LLM changed the transcript but isn't confident, ask before acting.
        # Skip entirely if the corrected text is a Tier 2 emergency — escalate now.
        elif not _tier2_now and confidence in ("medium", "low") and corrections and corrected != raw_transcript:
            bot_message = (
                f"Just to confirm — did you mean: \"{corrected}\"? "
                f"Say yes and I'll get right on it, or go ahead and rephrase if I got it wrong."
            )
            pending_correction = corrected
            action = "clarify"
            intent = "other"

            conversation_history.append({"role": "user",      "content": raw_transcript})
            conversation_history.append({"role": "assistant", "content": bot_message})
            # Note: total_turns is intentionally NOT incremented here —
            # a correction-confirmation question is not a real bot response.
            logger.process_gate("AWAITING CONFIRMATION", f"uncertain correction → '{corrected}'")
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
        if not is_gibberish and _tier2_now:
            logger.process_gate("TIER 2 DETECTED", f"rule-based match in: '{corrected[:60]}'")
            _urgent = _is_tier2_urgent(corrected) or _is_tier2_urgent(raw_transcript)
            if _urgent:
                bot_message = (
                    "I can hear the urgency — with only minutes to go you need hands-on help "
                    "right now, not a step-by-step walkthrough. I'm escalating this immediately "
                    "to a technician who can get to you straight away and get that machine up."
                )
            else:
                bot_message = (
                    "This sounds like it's affecting multiple users or a critical system — "
                    "that's a Tier 2 issue that needs immediate attention from our infrastructure "
                    "team. I'm creating a high-priority ticket right now and a specialist will "
                    "be in touch with you shortly."
                )
            action = "escalate"
            intent = "other"
            tier2_escalation = True

        # 4c. Total turn cap — fires if the session runs too long regardless of action type
        elif total_turns >= MAX_TURNS:
            logger.process_gate("TURN CAP", f"total turns {total_turns} >= {MAX_TURNS} — escalating")
            bot_message = (
                "We've been at this for a while and I haven't been able to fully resolve your "
                "issue — I'm going to escalate this to one of our human agents who can give "
                "you more personalised help. Thanks for your patience."
            )
            action = "escalate"
            intent = last_intent

        # 4d. Clarify wall
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

        # 4d. Hard escalate — all MAX_ATTEMPTS troubleshoot steps have been given.
        #     Always calls the LLM with is_final=True so it knows the limit is reached.
        #     The LLM uses action="explain" for sub-questions about the current step
        #     ("how do I do that?") and action="escalate" when the step has failed.
        #     Any action other than "escalate"/"close" is treated as a sub-question
        #     and answered without closing the session. Multiple sub-questions are
        #     allowed freely — only MAX_TURNS acts as the outer safety net.
        #     Safety net: if LLM ignores is_final and returns "troubleshoot" (new step),
        #     we force action="escalate" so the session always ends here.
        elif attempt_count >= MAX_ATTEMPTS:
            logger.process_gate("HARD ESCALATE CHECK", f"attempt_count {attempt_count} >= {MAX_ATTEMPTS} — is_final LLM call")
            rag_result  = rag_respond(corrected, conversation_history,
                                      attempt=attempt_count, is_final=True)
            action      = rag_result["action"]
            bot_message = rag_result["message"]
            intent      = rag_result.get("intent", last_intent)
            last_intent = intent
            clarify_count = 0

            if action == "troubleshoot":
                # LLM ignored is_final and proposed a new step — force escalate.
                logger.process_gate("HARD ESCALATE", "LLM returned troubleshoot despite is_final — forcing escalate")
                action = "escalate"
            elif action not in ("escalate", "close"):
                # explain / chat / clarify — sub-question answered, session stays open.
                logger.process_gate("SUB-QUESTION", f"action='{action}' — answering without escalating")

        else:
            # 4e. Normal RAG path — attempts 1, 2, and 3.
            #     The LLM never sees is_final=True here, so it proposes steps naturally
            #     without "last attempt" warnings. Escalation is driven by the gate above.
            rag_result  = rag_respond(corrected, conversation_history, attempt=attempt_count + 1)
            bot_message = rag_result["message"]
            action      = rag_result["action"]
            intent      = rag_result.get("intent", "other")
            last_intent = intent

            if action == "clarify":
                clarify_count += 1
                logger.process_clarify(clarify_count, MAX_CLARIFY)
            else:
                clarify_count = 0

            if action == "troubleshoot":
                attempt_count += 1
                troubleshoot_steps.append(bot_message)
                logger.process_attempt(attempt_count, MAX_ATTEMPTS)

        # 5. Update conversation history
        conversation_history.append({"role": "user",      "content": corrected})
        conversation_history.append({"role": "assistant", "content": bot_message})
        total_turns += 1

        # 6. TTS
        logger.bot_reply(bot_message)
        audio_b64 = await get_audio_base64(bot_message, resolve_voice_id(voice_id))

        # 7. Generate ticket on escalate or close; clear state on any session end
        ticket = None
        if action in ("escalate", "close"):
            logger.ticket_created(action, intent)
            session = {
                "caller_id": "Unknown",
                "tier": "2" if tier2_escalation else "1",
                "intent": intent,
                "raw_transcript": raw_transcript,
                "corrected_transcript": corrected,
                "corrections": correction_result.get("corrections", []),
                "steps_taken": list(troubleshoot_steps),
                "outcome": action,
                "escalation_reason": (
                    f"Hard limit reached after {MAX_ATTEMPTS} attempts"
                    if attempt_count >= MAX_ATTEMPTS
                    else f"RAG pipeline — action: {action}, intent: {intent}"
                )
            }
            ticket = generate_ticket(session)
            conversation_history  = []
            attempt_count         = 0
            clarify_count         = 0
            total_turns           = 0
            troubleshoot_steps    = []
            last_intent           = "other"
            tier2_escalation      = False

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
    global conversation_history, attempt_count, clarify_count, pending_correction, troubleshoot_steps, last_intent, tier2_escalation, total_turns
    conversation_history = []
    attempt_count        = 0
    clarify_count        = 0
    total_turns          = 0
    pending_correction   = None
    troubleshoot_steps   = []
    last_intent          = "other"
    tier2_escalation     = False
    print("[Session] Conversation history and all counters cleared.")
    return {"status": "ok"}

# ── Entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
