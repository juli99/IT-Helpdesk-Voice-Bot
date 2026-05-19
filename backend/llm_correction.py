from openai import OpenAI
from dotenv import load_dotenv
import os, json

load_dotenv()
token=os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")
client = OpenAI(
    api_key=token,
    base_url="https://api.groq.com/openai/v1"
)

def llm_correct(transcript: str, flagged: list, vocab_terms: list) -> dict:
    if not flagged:
        return {'corrected_transcript': transcript, 'confidence': 'high', 'corrections': []}
    try:

        prompt = f"""IT support ASR correction. Return JSON only. No preamble. No markdown.
        Transcript: {transcript}
        ONLY correct these specific words/phrases: {flagged}
        Known IT terms for reference: {vocab_terms}
        Rules:
        - Only modify words listed in the flagged list above
        - Do not correct any other words
        - If unsure, leave the original word unchanged
        Return exactly:
        {{
            "corrected_transcript": string,
            "confidence": "high" or "low",
            "corrections": [{{"original": string, "corrected": string}}]
        }}"""
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
            # או mixtral-8x7b-32768
        )
        return json.loads(res.choices[0].message.content)
    except Exception as e:
        print(f"[llm_correct] API error: {e}")
        return {'corrected_transcript': transcript, 'confidence': 'low', 'corrections': []}