from classify import classify

# 6 תמלולים לבדיקה לפי המסמך
transcripts = [
    # תרחיש A — Tier 1 VPN
    "I can't connect to the VPN while working from home, it keeps timing out.",

    # תרחיש B — Tier 1 Email עם ASR תיקון
    "My Outlook stopped syncing after the Active Directory authentication update.",

    # תרחיש C — Tier 2 מיידי
    "The SQL server is completely down, the whole office cannot access anything.",

    # בדיקות נוספות
    "I forgot my password and can't log into my computer.",
    "My laptop keeps crashing when I open the software.",
    "The production server is unreachable, customers cannot access the website."
]

print("=" * 60)
correct = 0
total = len(transcripts)

for i, transcript in enumerate(transcripts, 1):
    result = classify(transcript)
    tier = result['tier']
    intent = result['intent']
    reason = result['reason']

    marker = "🔴 TIER 2" if tier == '2' else "🟢 TIER 1"

    print(f"Test {i}: {marker} | intent: {intent}")
    print(f"Input:  {transcript}")
    print(f"Reason: {reason}")
    print("-" * 60)
