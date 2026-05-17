from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """You are an IT support call classifier.
Return JSON only. No preamble. No markdown.

Tier 2 triggers (ANY of these = tier 2):
- production/prod server down or unreachable
- whole office / everyone affected
- database down / SQL server unreachable
- Active Directory / domain controller completely down
- website down for all customers
- server room / rack / UPS failure

NOT tier 2 (these are tier 1):
- single user cannot log in
- Outlook not syncing for one person
- Active Directory mentioned but not completely down
- slow computer or internet for one user
- one file not accessible

Intent examples:
- vpn: cannot connect to VPN, VPN disconnecting, VPN timeout
- email: Outlook not syncing, email not working
- login: forgot password, can't log in, locked out
- network: internet slow, no internet, router issues
- software: app crashing, software not opening
- hardware: printer, mouse, keyboard, physical device
- other: anything that doesn't fit above

Return:
{
  "tier": "1" or "2",
  "intent": one of [vpn, email, login, network, software, hardware, other],
  "reason": one sentence
}"""


def classify(corrected_transcript: str) -> dict:
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=200,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": corrected_transcript}
        ]
    )

    try:
        result = json.loads(res.choices[0].message.content)
        assert 'tier' in result and 'intent' in result
        return result
    except:
        return {
            'tier': '1',
            'intent': 'other',
            'reason': 'classification failed'
        }
