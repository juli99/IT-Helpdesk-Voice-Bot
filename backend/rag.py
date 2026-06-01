"""
rag.py — Retrieval-Augmented Generation pipeline.

Provides:
  - retrieve(query)         → list of relevant text chunks from ChromaDB
  - rag_respond(query, history) → {message, action, intent}
"""

import os
import re
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
import chromadb
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import logger

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

load_dotenv(dotenv_path=ROOT_DIR / ".env")
load_dotenv(find_dotenv(usecwd=False))

DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "it_knowledge"

# ── Lazy-loaded singletons (avoid re-loading on every request) ──
_embed_model: SentenceTransformer | None = None
_collection = None
_groq_client: OpenAI | None = None


def _model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        print("[RAG] Loading sentence-transformer model...")
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def _collection_handle():
    global _collection
    if _collection is None:
        chroma = chromadb.PersistentClient(path=str(DB_DIR))
        _collection = chroma.get_collection(COLLECTION_NAME)
    return _collection


def _groq() -> OpenAI:
    global _groq_client
    if _groq_client is None:
        _groq_client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY") or os.getenv("API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    return _groq_client


# ── System prompt ────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are Alex, a friendly and professional IT helpdesk assistant.

You will receive:
  - RETRIEVED KNOWLEDGE: relevant excerpts from the IT knowledge base
  - ATTEMPT INFO: which attempt number this is (out of a maximum of 3)
  - The conversation so far

Your behaviour rules:
  1. Be warm and conversational — the user is having a frustrating time.
  2. Use the retrieved knowledge to give accurate, specific guidance.
  3. Suggest ONE clear action to try at a time. Do not dump a list of steps.
  4. After each fix, ask the user whether it worked.
  5. IMPORTANT — attempt strategy:
       Attempt 1: try the most common, straightforward fix for the issue.
       Attempt 2: try a different angle — a deeper or alternative fix.
       Attempt 3: try a third distinct approach (e.g. reinstall, reset, different tool).
     Each attempt must be meaningfully different from the previous ones.
  6. If the user says the issue is resolved, acknowledge it warmly and set action to "close".
  7. IMMEDIATELY escalate (action "escalate", do NOT troubleshoot) when the user reports:
       - More than one person affected: "everyone", "the whole team", "all of us", "nobody can"
       - Critical infrastructure down: production server, database, domain controller
       - A security incident: ransomware, breach, malware, hacking
       - Physical damage requiring on-site presence
       - A time-critical emergency: the user has a hard deadline in minutes (meeting, presentation,
         demo, call) AND a complete system failure (computer won't start/load/boot, total loss
         of access). There is no time for step-by-step troubleshooting — a human must intervene.
     Do not ask clarifying questions — escalate immediately.
  8. For greetings or general questions, respond naturally with action "chat".
  9. If the user's message is completely unintelligible, pure gibberish, random sounds,
     or so unclear that you genuinely cannot determine any intent — set action to "clarify"
     and politely ask them to rephrase. Do NOT guess or invent an issue.
  10. Do NOT escalate a single-user issue just because you are running low on ideas —
      the system enforces a hard attempt limit separately for that case.

Respond ONLY with valid JSON — no markdown, no preamble:
{
  "message": "<your spoken response>",
  "action": "troubleshoot" | "explain" | "escalate" | "close" | "chat" | "clarify",
  "intent": "vpn" | "email" | "login" | "network" | "software" | "hardware" | "other"
}

action definitions:
  troubleshoot — you are proposing a NEW step for the user to try; they will report back with the result
  explain      — you are elaborating on or walking through a step ALREADY proposed
                 (e.g. user asked "how do I do that?", "where do I find Control Panel?")
                 Use this when you are NOT introducing a new approach, just clarifying the current one
  escalate     — issue clearly needs a Tier 2 technician (infrastructure/security/physical)
  close        — user confirmed the issue is resolved
  chat         — greeting or general question before any troubleshooting has started
  clarify      — input was unintelligible or too vague to act on; asking user to rephrase
"""


# ── Retrieval ────────────────────────────────────────────────────
def retrieve(query: str, n_results: int = 4) -> list[str]:
    """Embed query and return top-N relevant knowledge chunks."""
    try:
        embedding = _model().encode([query])[0].tolist()
        results = _collection_handle().query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "distances", "metadatas"]
        )
        docs = results["documents"][0] if results["documents"] else []
        dists = results["distances"][0] if results["distances"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []

        # Cosine distance < 0.9 = meaningfully relevant (0–2 scale where 0 = identical)
        relevant = []
        for doc, dist, meta in zip(docs, dists, metas):
            if dist < 0.9:
                relevant.append(f"[{meta.get('topic', '?')}] {doc}")
            else:
                logger.rag_chunk_dropped(dist, doc)

        logger.rag_retrieval(len(relevant), n_results, query)
        return relevant

    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        return []


# ── JSON extraction helper ───────────────────────────────────────
def _extract_json(text: str) -> dict | None:
    """
    Robustly extract the first valid JSON object from LLM output.

    Handles:
      - Clean JSON responses           {"message": "...", ...}
      - Markdown-fenced responses      ```json\n{...}\n```
      - Text-then-JSON responses       "Here is my reply:\n{...}"
      - Nested braces inside strings   handled by balanced-brace scan
    """
    # 1. Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())

    # 2. Try the whole string first (the happy path)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Find the first '{' and scan for its matching '}'
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i+1]
                try:
                    result = json.loads(candidate)
                    assert isinstance(result, dict)
                    assert "message" in result and "action" in result
                    return result
                except Exception:
                    pass  # try wider next time

    return None


# ── Generation ───────────────────────────────────────────────────
def generate(query: str, history: list[dict], chunks: list[str], attempt: int, is_final: bool = False) -> dict:
    """Call Groq LLM with retrieved context, conversation history, and attempt number."""
    if chunks:
        context = "\n\n---\n\n".join(chunks)
    else:
        context = "No specific knowledge base entry found — use general IT best practices."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        # Inject retrieved knowledge and attempt info as a priming user turn
        {
            "role": "user",
            "content": (
                f"RETRIEVED KNOWLEDGE:\n{context}\n\n"
                f"ATTEMPT INFO: This is troubleshooting attempt {attempt} of 3. "
                f"{'Try the most common fix.' if attempt == 1 else ''}"
                f"{'The first approach did not work — try a different angle.' if attempt == 2 else ''}"
                f"{'Two approaches have already failed — try a third, distinct method.' if attempt == 3 else ''}"
                + (
                    "\n\nFINAL EXCHANGE: The troubleshooting attempt limit has been reached. "
                    "Two rules apply strictly from here:\n"
                    "1. If the user is asking HOW to carry out the step you just proposed "
                    "(e.g. 'how do I do that?', 'where is Control Panel?', 'what does that mean?') "
                    "— answer them fully and set action to 'explain'. Do NOT introduce any new approach.\n"
                    "2. If the user is reporting that the last step did not work, or they have no "
                    "further questions about it — set action to 'escalate' and give a warm wrap-up "
                    "letting them know a human agent will take over."
                    if is_final else ""
                )
                + f"\n\n---\nConversation begins now."
            )
        },
        {"role": "assistant", "content": "Understood. I'm ready to help."},
    ]

    # Append conversation history (last 10 turns to stay within token budget)
    messages.extend(history[-10:])

    # Current user message
    messages.append({"role": "user", "content": query})

    response = _groq().chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=350,
        temperature=0.45,
        response_format={"type": "json_object"},  # forces pure JSON output
        messages=messages
    )

    raw = response.choices[0].message.content.strip()

    result = _extract_json(raw)
    if result is None:
        print(f"[RAG] JSON parse failed entirely. Raw output: {raw[:300]}")
        # Last resort: use the raw text as the message so the user still hears something
        # Strip any JSON-looking tail so it doesn't leak into the spoken response
        clean = re.sub(r'\{.*', '', raw, flags=re.DOTALL).strip()
        return {
            "message": clean or "I'm sorry, could you rephrase that?",
            "action": "clarify",
            "intent": "other"
        }

    if "intent" not in result:
        result["intent"] = "other"
    return result


# ── Public entrypoint ────────────────────────────────────────────
def rag_respond(query: str, history: list[dict], attempt: int = 1, is_final: bool = False) -> dict:
    """
    Full RAG pipeline.

    Args:
        query:   The user's latest transcript (after correction).
        history: List of {"role": "user"|"assistant", "content": "..."} dicts.
        attempt: Current troubleshoot attempt number (1-3). Passed to the LLM
                 so it tailors each attempt to a genuinely different approach.

    Returns:
        {"message": str, "action": str, "intent": str}
    """
    chunks = retrieve(query)
    result = generate(query, history, chunks, attempt, is_final=is_final)
    logger.rag_result(result["action"], result.get("intent", "other"), attempt, 3)
    return result
