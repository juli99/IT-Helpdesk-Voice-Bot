import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from tts import get_audio_base64
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    text: str
    voice_id: str

@app.get("/")
async def serve_home():
    return FileResponse('static/index.html')

@app.post("/speak")
async def speak_handler(request: ChatRequest):
    if request.voice_id == "female":
        v_id = os.getenv("ELEVENLABS_VOICE_ID_FEMALE")
    else:
        v_id = os.getenv("ELEVENLABS_VOICE_ID_MALE")
    
    print(f"DEBUG: Attempting to get audio for voice: {v_id}")
    
    audio_data = await get_audio_base64(request.text, v_id)
    
    if audio_data is None:
        print("DEBUG: get_audio_base64 returned NONE!") 
        return {"audio": ""}
        
    print(f"DEBUG: Success! Audio data length: {len(audio_data)}")
    return {"audio": audio_data}

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run("routing:app", host="127.0.0.1", port=8000, reload=True)