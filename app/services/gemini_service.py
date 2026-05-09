import google.generativeai as genai
from app.config import settings
import logging

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """Bạn là trợ lý AI thông minh, thân thiện và hữu ích.
- Luôn trả lời bằng ngôn ngữ của người dùng
- Ngắn gọn, rõ ràng, đúng trọng tâm
- Nếu không biết, hãy thành thật nói không biết"""

model = genai.GenerativeModel(
    model_name=settings.GEMINI_MODEL,
    system_instruction=SYSTEM_PROMPT
)


def _sanitize_history(history: list[dict]) -> list[dict]:
    """
    Gemini yêu cầu history xen kẽ user/model, bắt đầu bằng user.
    Hàm này loại bỏ các tin trùng role liên tiếp để tránh crash.
    """
    sanitized = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "").strip()
        if not content:
            continue  # Bỏ qua tin rỗng
        if sanitized and sanitized[-1]["role"] == role:
            continue  # Bỏ qua nếu role trùng liên tiếp
        sanitized.append({"role": role, "parts": [content]})

    # Gemini history phải bắt đầu bằng "user"
    while sanitized and sanitized[0]["role"] != "user":
        sanitized.pop(0)

    return sanitized


async def chat(history: list[dict], user_message: str) -> str:
    """
    Gửi tin nhắn tới Gemini kèm lịch sử hội thoại.
    history: list of {"role": "user"/"model", "content": "..."}
    """
    gemini_history = _sanitize_history(history)
    chat_session = model.start_chat(history=gemini_history)
    response = await chat_session.send_message_async(user_message)
    return response.text
