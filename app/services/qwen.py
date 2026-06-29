import httpx
from ollama import AsyncClient

class QwenService:
    def __init__(self):
        self.client = AsyncClient(host="http://localhost:11434")
        self.model_name = "qwen3.5:9b"
    
    async def generate_response(self, 
        user_text: str,
    ) -> str:
        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": user_text}],
            )
            return response.message.content
        except httpx.RequestError as e:
            return f"Request error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"