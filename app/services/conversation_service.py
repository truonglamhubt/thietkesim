from datetime import datetime
from app.database.mongodb import get_db
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def get_history(user_id: int) -> list[dict]:
    """Lấy lịch sử hội thoại gần nhất của user."""
    db = get_db()
    doc = await db.conversations.find_one(
        {"user_id": user_id},
        {"messages": {"$slice": -settings.MAX_HISTORY}}  # Lấy N tin cuối
    )
    if not doc:
        return []
    return doc.get("messages", [])

async def add_message(user_id: int, username: str, role: str, content: str):
    """Thêm 1 tin nhắn vào lịch sử của user."""
    db = get_db()
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    }
    await db.conversations.update_one(
        {"user_id": user_id},
        {
            "$push": {"messages": message},
            "$set": {
                "username": username,
                "updated_at": datetime.utcnow()
            },
            "$setOnInsert": {"created_at": datetime.utcnow()}
        },
        upsert=True
    )

async def clear_history(user_id: int):
    """Xóa toàn bộ lịch sử của user."""
    db = get_db()
    await db.conversations.update_one(
        {"user_id": user_id},
        {"$set": {"messages": [], "updated_at": datetime.utcnow()}}
    )

async def get_stats(user_id: int) -> dict:
    """Thống kê hội thoại của user."""
    db = get_db()
    doc = await db.conversations.find_one({"user_id": user_id})
    if not doc:
        return {"total_messages": 0}
    msgs = doc.get("messages", [])
    return {
        "total_messages": len(msgs),
        "user_messages": sum(1 for m in msgs if m["role"] == "user"),
        "ai_messages": sum(1 for m in msgs if m["role"] == "model"),
    }
