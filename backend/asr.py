import whisper
import os

model = whisper.load_model("small")

def return_transcription(audio_path: str) -> str:
    result = model.transcribe(audio_path, temperature=0)
    return result['text'].strip()