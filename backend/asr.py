import whisper
import os

model = whisper.load_model("tiny")

def return_transcription(audio_path: str) -> str:
    try:
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            return ""
        
        result = model.transcribe(audio_path, temperature=0, language="en")
        return result['text'].strip()

    except Exception as e:
        print(f"[ASR ERROR] Transcription failed: {e}")
        return ""