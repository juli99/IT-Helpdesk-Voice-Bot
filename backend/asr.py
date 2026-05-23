import whisper
import os
import logger

# "base" is ~4x more accurate than "tiny" with acceptable CPU speed.
# Change to "small" for even better accuracy (slower first load).
model = whisper.load_model("base")

# Priming prompt that biases Whisper toward IT vocabulary.
# It never appears in the output — it just shifts the language model's priors.
IT_PROMPT = (
    "IT helpdesk call. Common terms: VPN, Outlook, Active Directory, Microsoft 365, "
    "Wi-Fi, Ethernet, DHCP, DNS, IP address, password reset, two-factor authentication, "
    "MFA, authenticator, OneDrive, SharePoint, printer, Bluetooth, USB, HDMI, "
    "blue screen, BSOD, Task Manager, Device Manager, firewall, antivirus, "
    "remote desktop, RDP, Teams, Zoom, Excel, Word, PowerPoint."
)

def return_transcription(audio_path: str) -> str:
    try:
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            return ""

        result = model.transcribe(
            audio_path,
            language="en",
            initial_prompt=IT_PROMPT,         # biases recognition toward IT terms
            temperature=0.0,                  # deterministic decode
            condition_on_previous_text=False,  # prevents hallucination loops
            no_speech_threshold=0.6,           # skip segments that are likely silence
            logprob_threshold=-1.0,            # discard low-confidence segments
        )

        # Filter out Whisper's common hallucinations on silence/noise
        text = result["text"].strip()
        HALLUCINATIONS = {
            "thank you", "thanks for watching", "thank you for watching",
            "subscribe", "you", ".", "", " "
        }
        if text.lower() in HALLUCINATIONS or len(text) < 2:
            logger.asr_empty()
            return ""

        logger.asr_raw(text)
        return text

    except Exception as e:
        print(f"[ASR ERROR] Transcription failed: {e}")
        return ""
