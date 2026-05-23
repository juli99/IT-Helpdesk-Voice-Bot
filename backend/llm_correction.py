"""
llm_correction.py — LLM-based ASR correction for IT support transcripts.

Always runs (even when fuzzy matching found nothing), because Whisper can
mishear technical terms in ways that don't fuzzy-match any vocabulary entry.
The LLM uses the IT context to fix what fuzzy matching missed.
"""

import os
import re
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import logger

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")
load_dotenv(find_dotenv(usecwd=False))

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY") or os.getenv("API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """\
You are an ASR post-processor for an IT support helpdesk.
Whisper sometimes mishears technical terms — your job is to fix them.

Rules:
- NEVER add words that were not in the original transcript. Only replace or fix existing words.
- NEVER remove words from the transcript.
- Only fix words that are clearly a Whisper mishearing of a real IT term.
- Preserve the user's sentence structure exactly — do not rephrase or summarise.
- Common Whisper mistakes: "VPN" heard as "the PN", "Outlook" as "out look",
  "Active Directory" as "active rectory", "Wi-Fi" as "why fie",
  "HDMI" as "HD me", "DNS" as "the NS", "DHCP" as "D H CP".
- If the fuzzy_suggestions list contains a suggestion that would require ADDING a word,
  reject it — it is a false positive from the fuzzy matcher.
- If the transcript looks correct as-is, return it unchanged with confidence "high".
- Set confidence:
    "high"   — transcript is clearly intelligible and correct
    "medium" — transcript is understandable but had terms to fix
    "low"    — transcript is mostly unintelligible or too vague to act on

Return ONLY valid JSON — no markdown, no preamble:
{
  "corrected_transcript": string,
  "confidence": "high" | "medium" | "low",
  "corrections": [{"original": string, "corrected": string}]
}"""


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM output, stripping any markdown code fences."""
    # Strip ```json ... ``` or ``` ... ``` wrappers
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())
    return json.loads(text.strip())


def llm_correct(transcript: str, flagged: list, vocab_terms: list) -> dict:
    """
    Call the LLM to correct the transcript.

    Args:
        transcript:  Raw (or fuzzy-pre-corrected) ASR output.
        flagged:     List of {"original": str, "suggested": str} from fuzzy_check.
                     May be empty — the LLM still runs.
        vocab_terms: Subset of IT vocabulary relevant to the flagged words.

    Returns:
        {"corrected_transcript": str, "confidence": str, "corrections": list}
    """
    user_content_parts = [f'Transcript: "{transcript}"']

    if flagged:
        user_content_parts.append(f"Fuzzy suggestions (likely errors): {flagged}")
    else:
        user_content_parts.append(
            "No fuzzy suggestions — check independently for any misheard IT terms."
        )

    if vocab_terms:
        user_content_parts.append(f"Relevant IT terms for reference: {vocab_terms}")

    user_content = "\n".join(user_content_parts)

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=400,
            temperature=0.1,   # low temp — we want conservative, predictable corrections
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_content}
            ]
        )
        raw = res.choices[0].message.content
        result = _extract_json(raw)

        # Validate required fields
        assert "corrected_transcript" in result
        if "confidence" not in result:
            result["confidence"] = "medium"
        if "corrections" not in result:
            result["corrections"] = []

        # Tag each correction with its source for the terminal log
        fuzzy_suggested = {f["original"].lower() for f in flagged}
        for c in result["corrections"]:
            c["source"] = "Fuzzy+LLM" if c.get("original", "").lower() in fuzzy_suggested else "LLM"

        logger.llm_correction_result(
            original=transcript,
            corrected=result["corrected_transcript"],
            corrections=result["corrections"],
            confidence=result["confidence"]
        )
        return result

    except Exception as e:
        print(f"[llm_correct] Error: {e}")
        return {
            "corrected_transcript": transcript,
            "confidence": "low",
            "corrections": []
        }
