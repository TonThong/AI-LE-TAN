from faster_whisper import WhisperModel
from pathlib import Path
import traceback
import edge_tts

class VoiceService:
    def __init__(self):
        self.model = WhisperModel(
            "large-v3",
            device="cuda",
            compute_type="float16"
        )
        self.voice = "vi-VN-HoaiMyNeural"

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

    async def text_to_speech(self, text: str) -> bytes:
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate="+0%",
                volume="+0%",
                pitch="+0Hz",
            )

            audio_data = bytearray()

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])

            return bytes(audio_data)
        except Exception as e:
            traceback.print_exc()
            return f"Error: {str(e)}"  