import json
from pathlib import Path

import chromadb
from ollama import Client

BASE_DIR = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = BASE_DIR / "data" / "knowledge"
CHROMA_DIR = BASE_DIR / "data" / "chroma"

ollama_client = Client(host="http://localhost:11434")
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = chroma_client.get_or_create_collection(
    name="cafe_knowledge"
)

EMBEDDING_MODEL = "qwen3-embedding"

def build_menu_records() -> list[dict]:
    menu_path = KNOWLEDGE_DIR / "menu.json"
    items = json.loads(menu_path.read_text(encoding="utf-8"))

    records = []

    for item in items:
        document = (
            f"Tên món: {item['name']}\n"
            f"Loại: {item['category']}\n"
            f"Giá: {item['price']} đồng\n"
            f"Mô tả: {item['description']}\n"
            f"Còn bán: {'Có' if item['available'] else 'Không'}"
        )

        records.append({
            "id": f"menu:{item['id']}",
            "document": document,
            "metadata": {
                "type": "menu",
                "name": item["name"],
                "available": item["available"],
                "price": item["price"],
                "source": "menu.json"
            }
        })

    return records

def build_promotion_records() -> list[dict]:
    promotions_path = KNOWLEDGE_DIR / "promotions.json"
    promotions = json.loads(promotions_path.read_text(encoding="utf-8"))

    records = []

    for promo in promotions:
        document = (
            f"Tên chương trình: {promo['name']}\n"
            f"Mô tả: {promo['description']}\n"
            f"Điều kiện: {promo['condition']}\n"
            f"Áp dụng từ: {promo['valid_from']}\n"
            f"Áp dụng đến: {promo['valid_to']}\n"
            f"Active: {'Có' if promo['active'] else 'Không'}"
        )

        records.append({
            "id": f"promotion:{promo['id']}",
            "document": document,
            "metadata": {
                "type": "promotion",
                "name": promo["name"],
                "active": promo["active"],
                "source": "promotions.json"
            }
        })

    return records

def build_cafe_info_records() -> list[dict]:
    cafe_info_path = KNOWLEDGE_DIR / "cafe_info.json"
    cafe_info = json.loads(cafe_info_path.read_text(encoding="utf-8"))

    document = (
        f"Tên quán: {cafe_info['name']}\n"
        f"Địa chỉ: {cafe_info['address']}\n"
        f"Giờ mở cửa: {cafe_info['opening_hours']}\n"
        f"SĐT: {cafe_info['phone']}\n"
        f"Wi-Fi: {cafe_info['wifi']}\n"
        f"Nhạc: {cafe_info['music']}\n"
        f"Cho phép chụp ảnh: {cafe_info['photography']}\n"
        f"Khu vực ngoài trời: {cafe_info['outdoor_seating']}\n"
        f"Thanh toán: {cafe_info['payment']}\n"
        f"Đậu xe: {cafe_info['parking']}"
    )

    return [{
        "id": "cafe_info",
        "document": document,
        "metadata": {
            "type": "cafe_info",
            "name": cafe_info["name"],
            "source": "cafe_info.json"
        }
    }]

def ingest() -> None:
    records = (
        build_menu_records()
        + build_promotion_records()
        + build_cafe_info_records()
    )

    documents = [record["document"] for record in records]

    embedding_response = ollama_client.embed(
        model=EMBEDDING_MODEL,
        input=documents,
    )

    collection.upsert(
        ids=[record["id"] for record in records],
        documents=documents,
        metadatas=[record["metadata"] for record in records],
        embeddings=embedding_response.embeddings,
    )
    print(f"Đã index {len(records)} bản ghi.")

if __name__ == "__main__":
    ingest()