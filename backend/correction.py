import json
from pathlib import Path
from fuzzy_correction import fuzzy_check
from llm_correction import llm_correct
import logger

BASE_DIR = Path(__file__).resolve().parent


def load_vocab() -> list:
    with open(BASE_DIR / "it_vocab.json", "r", encoding="utf-8") as f:
        return json.load(f)["terms"]


def get_relevant_vocab(flagged: list, vocab_terms: list, max_terms: int = 25) -> list:
    if not flagged:
        return []
    matched = {f["matched_term"].lower() for f in flagged}
    flagged_words = {w for f in flagged for w in f["original"].lower().split()}
    relevant = [
        term for term in vocab_terms
        if term.lower() in matched or set(term.lower().split()) & flagged_words
    ]
    return relevant[:max_terms]


def correction(transcript: str) -> dict:
    """
    Two-stage correction pipeline:
      1. Fuzzy matching — fast, finds near-miss IT terms.
      2. LLM correction — always runs, catches what fuzzy missed.

    Returns:
        {
          "corrected_transcript": str,
          "confidence": "high" | "medium" | "low",
          "corrections": list
        }
    """
    vocab_terms = load_vocab()

    # Stage 1 — fuzzy
    flagged      = fuzzy_check(transcript, vocab_terms)
    flagged_clean = [
        {"original": f["original"], "suggested": f["matched_term"]}
        for f in flagged
    ]
    relevant_vocab = get_relevant_vocab(flagged, vocab_terms)

    # Stage 2 — LLM (always runs, even when flagged is empty)
    result = llm_correct(transcript, flagged_clean, relevant_vocab)

    # Accept a correction when ANY of these are true:
    #   a) The LLM's "original" exactly matches a fuzzy-flagged term.
    #   b) A fuzzy-flagged term is contained within the LLM's "original"
    #      (e.g. fuzzy flagged "pn", LLM corrected the wider phrase "the PN").
    #   c) The LLM is confident (high/medium) — it caught something fuzzy missed.
    fuzzy_originals = {f["original"].lower() for f in flagged}
    verified = []
    for c in result.get("corrections", []):
        orig = c.get("original", "").lower()
        fuzzy_hit = (
            orig in fuzzy_originals
            or any(fo in orig for fo in fuzzy_originals)
        )
        if fuzzy_hit or result.get("confidence") in ("high", "medium"):
            verified.append(c)

    # Apply corrections longest-first to avoid partial-replacement collisions
    verified.sort(key=lambda c: len(c.get("original", "")), reverse=True)
    corrected = transcript
    applied   = []
    for c in verified:
        orig, corr = c.get("original", ""), c.get("corrected", "")
        if orig and corr and orig != corr and orig in corrected:
            corrected = corrected.replace(orig, corr)
            applied.append(c)

    confidence = result.get("confidence", "low")
    logger.correction_summary(transcript, corrected, confidence)

    return {
        "corrected_transcript": corrected,
        "confidence": confidence,
        "corrections": applied,
    }
