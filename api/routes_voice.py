from fastapi import APIRouter, UploadFile, File
from .schemas import TtsRequest, ChatResponse
from .services import voice as voice_service

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


@router.post("/stt")
async def stt(audio_file: UploadFile = File(...)):
    return await voice_service.stt(audio_file)


@router.post("/tts")
async def tts(request: TtsRequest):
    return await voice_service.tts(request)


@router.post("/chat", response_model=ChatResponse)
async def voice_chat(audio_file: UploadFile = File(...), user_id: str = "voice_user"):
    return await voice_service.chat(audio_file, user_id)