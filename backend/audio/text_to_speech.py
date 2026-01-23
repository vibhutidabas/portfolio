"""Text to speech conversion"""
from gtts import gTTS
import base64
from io import BytesIO
from typing import Optional


def text_to_speech(text: str, lang: str = 'en') -> Optional[str]:
    """
    Convert text to speech and return base64 encoded audio
    
    Args:
        text: Text to convert
        lang: Language code (default: 'en')
        
    Returns:
        Base64 encoded audio string or None on error
    """
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
        return audio_base64
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        return None
