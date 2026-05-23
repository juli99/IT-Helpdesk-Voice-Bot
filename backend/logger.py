"""
logger.py — Shared terminal logging utility for the IT Voice Bot pipeline.

All pipeline stages import from here so the output style stays consistent.
"""

# ANSI colour codes — fall back gracefully if the terminal doesn't support them
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
BLUE   = "\033[34m"
MAGENTA= "\033[35m"
WHITE  = "\033[97m"

DIVIDER     = f"{DIM}{'─' * 60}{RESET}"
DIVIDER_FAT = f"{BOLD}{'═' * 60}{RESET}"


def section(title: str) -> None:
    """Print a bold section header — marks the start of a new request."""
    print(f"\n{DIVIDER_FAT}")
    print(f"{BOLD}{WHITE}  {title}{RESET}")
    print(DIVIDER_FAT)


def log(tag: str, colour: str, message: str) -> None:
    """Generic log line:  [TAG]  message"""
    print(f"{colour}{BOLD}[{tag}]{RESET}  {message}")


def divider() -> None:
    print(DIVIDER)


# ── Convenience wrappers used by each pipeline stage ────────────

def asr_raw(text: str) -> None:
    log("ASR", CYAN, f"Raw transcript  →  \"{text}\"")

def asr_empty() -> None:
    log("ASR", RED, "No speech detected — transcript is empty")


def fuzzy_none() -> None:
    log("FUZZY", DIM + WHITE, "No near-miss terms found")

def fuzzy_flagged(flags: list) -> None:
    log("FUZZY", YELLOW, f"{len(flags)} term(s) flagged:")
    for f in flags:
        print(f"         {YELLOW}'{f['original']}'{RESET}  →  "
              f"{YELLOW}'{f['matched_term']}'{RESET}  "
              f"{DIM}(score {f['score']}){RESET}")


def llm_correction_result(original: str, corrected: str,
                           corrections: list, confidence: str) -> None:
    changed = original.strip() != corrected.strip()
    if changed:
        log("LLM-FIX", GREEN, f"Transcript corrected  (confidence: {confidence})")
        for c in corrections:
            src = c.get("source", "LLM")
            print(f"         {GREEN}'{c['original']}'{RESET}  →  "
                  f"{GREEN}'{c['corrected']}'{RESET}  "
                  f"{DIM}[{src}]{RESET}")
    else:
        log("LLM-FIX", DIM + WHITE,
            f"No changes applied  (confidence: {confidence})")


def correction_summary(raw: str, corrected: str, confidence: str) -> None:
    divider()
    log("TRANSCRIPT", WHITE, f"Original   →  \"{raw}\"")
    if raw.strip() != corrected.strip():
        log("TRANSCRIPT", GREEN, f"Corrected  →  \"{corrected}\"")
    log("TRANSCRIPT", DIM + WHITE, f"Confidence →  {confidence}")


def rag_retrieval(n_retrieved: int, n_requested: int, query: str) -> None:
    divider()
    log("RAG", BLUE, f"Query      →  \"{query[:70]}{'...' if len(query) > 70 else ''}\"")
    log("RAG", BLUE, f"Retrieved  →  {n_retrieved}/{n_requested} relevant chunks")

def rag_chunk_dropped(dist: float, preview: str) -> None:
    print(f"         {DIM}[dropped dist={dist:.3f}]  {preview[:55]}...{RESET}")

def rag_result(action: str, intent: str, attempt: int, max_attempts: int) -> None:
    action_colour = {
        "troubleshoot": YELLOW,
        "escalate":     RED,
        "close":        GREEN,
        "clarify":      MAGENTA,
        "chat":         CYAN,
    }.get(action, WHITE)
    log("RAG", BLUE,
        f"Intent     →  {BOLD}{intent}{RESET}")
    log("RAG", action_colour,
        f"Action     →  {BOLD}{action}{RESET}"
        + (f"  {DIM}(attempt {attempt}/{max_attempts}){RESET}"
           if action == "troubleshoot" else ""))


def process_gate(gate: str, detail: str = "") -> None:
    divider()
    log("GATE", RED, f"{gate}  {DIM}{detail}{RESET}")

def process_attempt(current: int, maximum: int) -> None:
    bar = ("█" * current) + ("░" * (maximum - current))
    log("ATTEMPT", YELLOW, f"[{bar}]  {current}/{maximum}")

def process_clarify(count: int, maximum: int) -> None:
    log("CLARIFY", MAGENTA, f"Unintelligible streak  →  {count}/{maximum}")

def bot_reply(message: str) -> None:
    divider()
    log("BOT", GREEN, f"\"{message[:120]}{'...' if len(message) > 120 else ''}\"")
    print(DIVIDER_FAT + "\n")

def ticket_created(action: str, intent: str) -> None:
    log("TICKET", RED, f"Created  →  action={action}  intent={intent}")
