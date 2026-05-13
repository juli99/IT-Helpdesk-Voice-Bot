# testing
import base64
import io
import os
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

FREE_VOICES = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Domi": "AZnzlk1XvdvUeBnXmlld",
    "Bella": "EXAVITQu4vr4xnSDxMaL",
    "Elli": "MF3mGyEYCl7XYWbV9V6O",
}

VOICE_NAME = "Bella"
VOICE_ID = FREE_VOICES[VOICE_NAME]


def speak(text: str, mp3_filename="output.mp3") -> str:

    audio = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        text=text,
        model_id="eleven_turbo_v2"
    )

    buf = io.BytesIO()

    for chunk in audio:
        buf.write(chunk)

    buf.seek(0)

    audio_bytes = buf.read()

    with open(mp3_filename, "wb") as f:
        f.write(audio_bytes)

    print(f"MP3 saved to: {mp3_filename}")

    return base64.b64encode(audio_bytes).decode("utf-8")


if __name__ == "__main__":

    print("Starting TTS test...\n")

    try:

        result = speak(
            "Hello Ido, your voice bot is working perfectly!"
        )

        print("Success!")
        print(f"Voice used: {VOICE_NAME}")
        print(f"Base64 length: {len(result)}")
        print(f"First 50 chars: {result[:50]}...")

    except Exception as e:

        print("Error during TTS execution:")
        print(e)