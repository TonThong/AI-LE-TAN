from pathlib import Path

from io import BytesIO
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import tempfile

from app.services.voice import VoiceService
from app.agent.orchestrator import ConversationOrchestrator
from app.schemas.conversation import ChatMessage

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AI Lễ Tân")
voice_service = VoiceService()
orchestrator = ConversationOrchestrator()

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

history_adapter = TypeAdapter(list[ChatMessage])

class SynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

@app.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    history: str = Form("[]"),
    ):
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File gửi lên không phải audio")

    suffix = Path(audio.filename or "recording.webm").suffix or ".webm"

    try:
        parsed_history = history_adapter.validate_json(history)
    except ValidationError:
        raise HTTPException(
            status_code=422,
            detail="Lịch sử hội thoại không hợp lệ",
        )
    
    history_messages = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in parsed_history[-20:]
    ]

    try:
        audio_bytes = await audio.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)

        text = await voice_service.speech_to_text(temp_path)
        qwen_response = await orchestrator.process(text, history=history_messages)

        return {
            "text": text,
            "qwen_response": qwen_response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/synthesize")
async def synthesize_audio(request: SynthesizeRequest):
    try:
        audio_bytes = await voice_service.text_to_speech(request.text)

        if not audio_bytes:
            raise HTTPException(
                status_code=500,
                detail="Không tạo được âm thanh",
            )

        return StreamingResponse(
            BytesIO(audio_bytes),
            media_type="audio/mpeg",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))