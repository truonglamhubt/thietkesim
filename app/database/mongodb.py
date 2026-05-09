from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db_state = Database()


async def connect_db():
    """Kết nối MongoDB Atlas khi app khởi động."""
    try:
        db_state.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000
        )
        db_state.db = db_state.client.chatbot
        await db_state.db.conversations.create_index("user_id", unique=True)
        logger.info("✅ MongoDB connected successfully")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def close_db():
    """Đóng kết nối khi app shutdown."""
    if db_state.client:
        db_state.client.close()
        logger.info("MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    return db_state.db
