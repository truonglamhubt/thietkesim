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

async def chat(history: list[dict], user_message: str) -> str:
    """
    Gửi tin nhắn tới Gemini kèm lịch sử hội thoại.
    history: list of {"role": "user"/"model", "content": "..."}
    """
    # Chuyển định dạng DB → Gemini format
    gemini_history = [
        {"role": msg["role"], "parts": [msg["content"]]}
        for msg in history
    ]

    chat_session = model.start_chat(history=gemini_history)
    response = await chat_session.send_message_async(user_message)
    return response.text
