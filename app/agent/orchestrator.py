from app.rag.retriever import CafeRetriever
from app.services.qwen import QwenService


class ConversationOrchestrator:
    def __init__(self):
        self.retriever = CafeRetriever()
        self.qwen = QwenService()

    async def process(self, 
        user_text: str,
        history: list[dict] | None = None,
    ) -> str:
        contexts = await self.retriever.search(
            query=user_text,
            top_k=4,
        )

        return await self.qwen.generate_response(
            user_text=user_text,
            context=contexts,
            history=history or [],
        )