from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import tempfile

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AI Lễ Tân")

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

@app.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/voice/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File gửi lên không phải audio")

    suffix = Path(audio.filename or "recording.webm").suffix or ".webm"

    try:
        audio_bytes = await audio.read()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        # Gọi service STT của bạn ở đây
        # Ví dụ:
        # text = voice_service.speech_to_text(audio_bytes, audio.filename, audio.content_type)

        text = "Kết quả speech to text ở đây"

        return {
            "text": text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))