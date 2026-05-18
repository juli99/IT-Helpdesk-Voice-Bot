import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def load_json_file(filename: str) -> dict:
    try:
        with open(BASE_DIR / filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Routing] Error loading {filename}: {e}")
        return {}

def route(tier: str, intent: str, step: int, resolved: bool) -> dict:
    print(f"[Routing Module] Incoming -> Tier: {tier}, Intent: {intent}, Step: {step}, Resolved: {resolved}")
    
    vocab_data = load_json_file("it_vocab.json")
    kb_data = load_json_file("kb.json")
    
    intent_lower = intent.lower() if intent else "other"

    if resolved:
        return {
            "action": "close",
            "message": "Excellent! I am glad we were able to resolve the issue. Thank you for contacting IT support. Have a wonderful day!",
            "reason": "User confirmed issue resolution"
        }

    tier2_triggers = vocab_data.get("tier2_triggers", [])
    if tier == "Tier 2" or any(trigger.lower() in intent_lower for trigger in tier2_triggers):
        return {
            "action": "escalate",
            "message": "This issue requires specialized assistance from our desktop support team. I am transferring your ticket to a Tier 2 technician now.",
            "reason": f"Immediate escalation triggered by tier2_triggers or classification tier for: {intent}"
        }

    topic = next((key for key in kb_data if key in intent_lower), "other")
    steps = kb_data.get(topic, kb_data.get("other", []))

    if step >= len(steps):
        return {
            "action": "escalate",
            "message": "We have gone through all standard remote troubleshooting steps, but the issue persists. I am creating a high-priority ticket.",
            "reason": f"Exhausted all {len(steps)} dynamic steps for topic: {topic}"
        }

    return {
        "action": "troubleshoot",
        "message": steps[step]
    }