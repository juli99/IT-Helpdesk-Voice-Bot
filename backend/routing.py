import os
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from faster_whisper import WhisperModel

from classify import classify
from correction import correction
from tts import get_audio_base64

BASE_DIR = Path(__file__).resolve().parent  
ROOT_DIR = BASE_DIR.parent               
FRONTEND_DIR = ROOT_DIR / "frontend"

load_dotenv(dotenv_path=ROOT_DIR / ".env")

whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    text: str
    voice_id: str

@app.get("/")
async def serve_home():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/knowledge_base.js")
async def get_kb():
    return FileResponse(ROOT_DIR / "knowledge_base.js")

@app.post("/speak")
async def speak_handler(request: ChatRequest):
    v_id = os.getenv("ELEVENLABS_VOICE_ID_FEMALE") if request.voice_id == "female" else os.getenv("ELEVENLABS_VOICE_ID_MALE")
    audio_data = await get_audio_base64(request.text, v_id)
    return {"audio": audio_data if audio_data else ""}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{datetime.now().timestamp()}.wav"
    try:
        with open(temp_filename, "wb") as buffer:
            buffer.write(await file.read())
        
        segments, _ = whisper_model.transcribe(temp_filename)
        raw_text = " ".join([s.text for s in segments])
        os.remove(temp_filename)

        correction = llm_correct(raw_text, flagged=[], vocab_terms=[])
        corrected_text = correction['corrected_transcript']
        
        classification = classify(corrected_text)
        
        return {
            "text": corrected_text, 
            "intent": classification['intent'],
            "tier": classification['tier'],
            "metadata": classification
        }
    except Exception as e:
        if os.path.exists(temp_filename): os.remove(temp_filename)
        print(f"Error: {e}")
        return {"error": str(e)}

app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

if __name__ == "__main__":
    uvicorn.run("routing:app", host="127.0.0.1", port=8000, reload=True)