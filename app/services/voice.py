from faster_whisper import WhisperModel
from pathlib import Path
import traceback

class VoiceService:
    def __init__(self):
        self.model = WhisperModel(
            "large-v3",
            device="cuda",
            compute_type="float16"
        )

    async def speech_to_text(self, audio_path: Path) -> str:
        try:
            segments, info = self.model.transcribe(
                str(audio_path),
                language="vi",
                vad_filter=True,
            )
            text = " ".join(segment.text.strip() for segment in segments)
            return text
            
        except Exception as e:
            traceback.print_exc()
            return f"Error: {str(e)}"