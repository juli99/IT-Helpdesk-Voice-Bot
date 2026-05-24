import whisper
import os
import json
from pathlib import Path
import logger

BASE_DIR = Path(__file__).resolve().parent

# ── Load IT vocabulary ────────────────────────────────────────────
with open(BASE_DIR / "it_vocab.json") as _f:
    _vocab = json.load(_f)

_terms = _vocab.get("terms", [])

# Build Whisper's initial_prompt from the vocab:
#   - Prefer single-word ALL-CAPS acronyms (VPN, DNS, MFA …) — most likely to be
#     misheard; pick first, they're the highest-value bias tokens.
#   - Then include a selection of common multi-word phrases.
#   - Keep the prompt under ~200 tokens so it doesn't eat the audio context window.
_acronyms   = [t for t in _terms if len(t.split()) == 1 and t == t.upper() and len(t) >= 2]
_multi_word = [t for t in _terms if len(t.split()) > 1][:40]   # cap at 40 phrases

_prompt_terms = _acronyms + _multi_word
IT_PROMPT = "IT helpdesk call. Common terms: " + ", ".join(_prompt_terms[:80]) + "."

# "tiny" is fast but less accurate. Switch to "base" for better accuracy on slower machines.
model = whisper.load_model("tiny")


def return_transcription(audio_path: str) -> str:
    try:
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            return ""

        result = model.transcribe(
            audio_path,
            language="en",
            initial_prompt=IT_PROMPT,          # biases recognition toward IT terms
            temperature=0.0,                   # deterministic decode
            condition_on_previous_text=False,  # prevents hallucination loops
            no_speech_threshold=0.6,           # skip segments that are likely silence
            logprob_threshold=-1.0,            # discard low-confidence segments
        )

        text = result["text"].strip()

        # Whisper produces these on genuinely silent or near-silent audio — discard them.
        # Do NOT add real phrases here (e.g. "thank you") — users may actually say them.
        SILENCE_OUTPUTS = {"", ".", "..", "...", " "}
        if text in SILENCE_OUTPUTS or len(text) < 2:
            logger.asr_empty()
            return ""

        logger.asr_raw(text)
        return text

    except Exception as e:
        print(f"[ASR ERROR] Transcription failed: {e}")
        return ""
