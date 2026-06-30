from pathlib import Path

import chromadb
from ollama import AsyncClient

BASE_DIR = Path(__file__).resolve().parents[2]
CHROMA_DIR = BASE_DIR / "data" / "chroma"

class CafeRetriever:
    def __init__(self):
        self.ollama = AsyncClient(host="http://localhost:11434")
        self.embedding_model = "qwen3-embedding"

        chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = chroma.get_or_create_collection(
            name="cafe_knowledge"
        )
    
    async def search(self, query: str, top_k: int = 4) -> list[dict]:
        
        if not query.strip() or self.collection.count() == 0:
            return []

        response = await self.ollama.embeddings(
            model=self.embedding_model,
            prompt=query
        )
        
        results = self.collection.query(
            query_embeddings=[response.embedding],
            n_results=min(top_k,self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            {
                "content": document,
                "metadata": metadata,
                "distance": distance,
            }
            for document, metadata, distance
            in zip(documents, metadatas, distances)
        ]
