from classify import classify

# רשימת מקרי קצה לבדיקה
edge_cases = [
    # Tier 2 מיידי
    "The production server is completely down",
    "The whole office cannot access anything",
    "Our database is unreachable",
    "Active Directory is down",
    "The website is down for all customers",

    # Tier 1 רגיל
    "My VPN keeps disconnecting",
    "I can't log into my computer",
    "Outlook stopped syncing",
    "My printer is not working",
    "The software keeps crashing",

    # מקרי גבול — קשה להחליט
    "My computer is slow",
    "I forgot my password",
    "The internet is slow today",
    "I can't access one file on the server",
    "My mouse is not working"
]

print("=" * 50)
for case in edge_cases:
    result = classify(case)
    tier = result['tier']
    intent = result['intent']
    reason = result['reason']
    
    # סימון ויזואלי — Tier 2 מסומן באדום
    marker = "🔴 TIER 2" if tier == '2' else "🟢 TIER 1"
    
    print(f"{marker} | intent: {intent}")
    print(f"Input:  {case}")
    print(f"Reason: {reason}")
    print("-" * 50)