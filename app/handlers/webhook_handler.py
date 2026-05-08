import httpx
from app.config import settings
from app.services import conversation_service, gemini_service
import logging

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

# ── Telegram helpers ──────────────────────────────────────────────────────────

async def send_message(chat_id: int, text: str, parse_mode: str = "Markdown"):
    """Gửi tin nhắn về Telegram."""
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        })
        if r.status_code != 200:
            logger.error(f"Telegram send error: {r.text}")

async def send_typing(chat_id: int):
    """Hiển thị trạng thái 'đang gõ...'."""
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendChatAction", json={
            "chat_id": chat_id,
            "action": "typing"
        })

# ── Command handlers ──────────────────────────────────────────────────────────

async def cmd_start(chat_id: int, username: str):
    await send_message(chat_id,
        f"👋 Xin chào *{username}*!\n\n"
        f"Mình là *{settings.BOT_NAME}* — trợ lý AI powered by Gemini ✨\n\n"
        f"Hãy gõ bất cứ điều gì để bắt đầu trò chuyện!\n"
        f"Dùng /help để xem các lệnh."
    )

async def cmd_help(chat_id: int):
    await send_message(chat_id,
        "*📋 Các lệnh có sẵn:*\n\n"
        "/start — Chào mừng\n"
        "/clear — 🗑️ Xóa lịch sử hội thoại\n"
        "/stats — 📊 Thống kê hội thoại\n"
        "/help — ❓ Trợ giúp"
    )

async def cmd_clear(chat_id: int, user_id: int):
    await conversation_service.clear_history(user_id)
    await send_message(chat_id, "🗑️ Đã xóa lịch sử hội thoại! Bắt đầu cuộc trò chuyện mới nào 🚀")

async def cmd_stats(chat_id: int, user_id: int):
    stats = await conversation_service.get_stats(user_id)
    await send_message(chat_id,
        f"📊 *Thống kê hội thoại của bạn:*\n\n"
        f"💬 Tổng tin nhắn: `{stats['total_messages']}`\n"
        f"👤 Tin của bạn: `{stats['user_messages']}`\n"
        f"🤖 Tin của AI: `{stats['ai_messages']}`"
    )

# ── Main update handler ───────────────────────────────────────────────────────

async def handle_update(update: dict):
    """Entry point xử lý mọi Telegram update."""
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    username = message["from"].get("username") or message["from"].get("first_name", "User")
    text = message.get("text", "").strip()

    if not text:
        return

    # Route commands
    if text.startswith("/start"):
        await cmd_start(chat_id, username)
        return
    if text.startswith("/help"):
        await cmd_help(chat_id)
        return
    if text.startswith("/clear"):
        await cmd_clear(chat_id, user_id)
        return
    if text.startswith("/stats"):
        await cmd_stats(chat_id, user_id)
        return

    # Chat thường → Gemini
    await send_typing(chat_id)

    try:
        history = await conversation_service.get_history(user_id)
        await conversation_service.add_message(user_id, username, "user", text)

        ai_reply = await gemini_service.chat(history, text)

        await conversation_service.add_message(user_id, username, "model", ai_reply)
        await send_message(chat_id, ai_reply)

    except Exception as e:
        logger.exception(f"Error handling message from user {user_id}")
        await send_message(chat_id, "❌ Có lỗi xảy ra, vui lòng thử lại sau.")
