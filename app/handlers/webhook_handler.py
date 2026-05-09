import httpx
from app.config import settings
from app.services import conversation_service, gemini_service
import logging

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

_http_client: httpx.AsyncClient = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def send_message(chat_id: int, text: str, parse_mode: str = "Markdown"):
    client = get_http_client()
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    try:
        r = await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)
        if r.status_code != 200 and "parse_mode" in payload:
            logger.warning(f"Markdown failed, retry plain text: {r.text}")
            payload.pop("parse_mode")
            await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)
    except Exception as e:
        logger.error(f"Lỗi gửi tin nhắn: {e}")


async def send_typing(chat_id: int):
    client = get_http_client()
    await client.post(f"{TELEGRAM_API}/sendChatAction", json={
        "chat_id": chat_id,
        "action": "typing"
    })


async def handle_update(update: dict):
    message = update.get("message") or update.get("edited_message")
    if not message or "text" not in message:
        return

    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    username = message["from"].get("first_name", "Khách")
    text = message["text"].strip()

    if text.startswith("/start"):
        await send_message(chat_id,
            f"👋 Chào anh *{username}*!\n\n"
            f"Em là trợ lý tư vấn từ *Thietkesim.vn* ✨\n\n"
            f"Anh cần em hỗ trợ gì về sim số đẹp không ạ?"
        )
        return

    if text.startswith("/clear"):
        await conversation_service.clear_history(user_id)
        await send_message(chat_id,
            "🗑️ Đã làm mới cuộc hội thoại!\n"
            "Anh cần em hỗ trợ gì mới không ạ?"
        )
        return

    await send_typing(chat_id)

    try:
        history = await conversation_service.get_history(user_id)
        await conversation_service.add_message(user_id, username, "user", text)
        ai_reply = await gemini_service.chat(history, text)
        await conversation_service.add_message(user_id, username, "model", ai_reply)
        await send_message(chat_id, ai_reply)

    except Exception as e:
        logger.exception(f"Lỗi xử lý tin nhắn từ user {user_id}")
        await send_message(chat_id,
            "Dạ em đang bận chút việc, anh vui lòng nhắn lại sau ít phút "
            "hoặc để lại số điện thoại em gọi lại ngay ạ! 🙏"
        )
