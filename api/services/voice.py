from fastapi import UploadFile
from .. import main as api_main
from ..schemas import ChatResponse


async def stt(audio_file: UploadFile):
    return await api_main.speech_to_text(audio_file)


async def tts(request):
    return await api_main.text_to_speech(request)


async def chat(audio_file: UploadFile, user_id: str = "voice_user") -> ChatResponse:
    return await api_main.voice_chat(audio_file, user_id)