import os
import httpx
import base64

async def get_audio_base64(text: str, voice_id: str):
    api_key = os.getenv("ELEVENLABS_API_KEY")

    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY is not set!")
        return None
    if not voice_id:
        print("ERROR: voice_id is None or empty!")
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    data = {
        "text": text,
        "model_id": "eleven_turbo_v2_5", 
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=data, headers=headers)
            if response.status_code != 200:
                print(f"ElevenLabs API Error: {response.status_code} - {response.text}")
                return None
            return base64.b64encode(response.content).decode('utf-8')
        except httpx.TimeoutException:
            print("ERROR: Request to ElevenLabs timed out")
            return None
        except Exception as e:
            print(f"Exception in get_audio_base64: {e}")
            return None