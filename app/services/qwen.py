import httpx
from ollama import AsyncClient
from app.agent.prompts import SYSTEM_PROMPT, build_user_prompt

class QwenService:
    def __init__(self):
        self.client = AsyncClient(host="http://localhost:11434")
        self.model_name = "qwen3.5:9b"
    
    async def generate_response(self, 
        user_text: str,
        context: list[dict],
    ) -> str:
        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(user_text, context)}
                ],
                think=False,
                options={
                    "num_predict": 90,
                }
            )
            return response.message.content.strip()
        except httpx.RequestError as e:
            return f"Request error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"