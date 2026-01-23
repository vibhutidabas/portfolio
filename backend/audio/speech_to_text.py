"""Speech to text conversion"""
# This module handles client-side speech recognition
# The actual recognition happens in the browser using Web Speech API
# This file is for future server-side STT if needed

def speech_to_text(audio_data: bytes) -> str:
    """
    Convert audio to text (future implementation)
    
    Args:
        audio_data: Audio bytes
        
    Returns:
        Transcribed text
    """
    # Can be implemented with services like:
    # - Google Cloud Speech-to-Text
    # - Azure Speech Services
    # - OpenAI Whisper
    pass
