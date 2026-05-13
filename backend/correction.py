from openai import OpenAI
from dotenv import load_dotenv
import os, json

load_dotenv()
token=os.getenv("API_KEY")
client = OpenAI(
    api_key=token,
    base_url="https://api.groq.com/openai/v1"
)

def llm_correct(transcript: str, flagged: list, vocab_terms: list) -> dict:
    if not flagged:
        return {
            'corrected_transcript': transcript,
            'confidence': 'high',
            'corrections': []
        }

    prompt = f"""IT support ASR correction. Return JSON only. No preamble. No markdown.

Transcript: {transcript}
Possibly misheard: {flagged}
Known IT terms: {vocab_terms}

Return exactly:
{{
    "corrected_transcript": string,
    "confidence": "high" or "low",
    "corrections": [{{"original": string, "corrected": string}}]
}}"""

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # או mixtral-8x7b-32768
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    )

    try:
        return json.loads(res.choices[0].message.content)
    except (json.JSONDecodeError, IndexError):
        return {
            'corrected_transcript': transcript,
            'confidence': 'low',
            'corrections': []
        }