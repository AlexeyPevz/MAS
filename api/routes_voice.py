from fastapi import APIRouter, UploadFile, File
from fastapi import HTTPException
from .schemas import TtsRequest, ChatResponse
from . import main as api_main

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


@router.post("/stt")
async def stt(audio_file: UploadFile = File(...)):
	return await api_main.speech_to_text(audio_file)


@router.post("/tts")
async def tts(request: TtsRequest):
	return await api_main.text_to_speech(request)


@router.post("/chat", response_model=ChatResponse)
async def voice_chat(audio_file: UploadFile = File(...), user_id: str = "voice_user"):
	return await api_main.voice_chat(audio_file, user_id)