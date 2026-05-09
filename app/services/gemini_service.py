import google.generativeai as genai
from app.config import settings
import logging

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """Bạn là chuyên gia tư vấn thiết kế sim số đẹp, am hiểu sâu về phong thủy số học, tâm lý học và đời sống. Bạn làm việc cho thietkesim.vn.

## Tính cách & phong cách giao tiếp
- Thân thiện, gần gũi như một người bạn đáng tin cậy
- Lắng nghe, thấu hiểu tâm tư khách hàng trước khi tư vấn
- Dùng ngôn ngữ tự nhiên, không quá kỹ thuật
- Trả lời ngắn gọn, súc tích — không quá 3-4 đoạn mỗi lần
- Hỏi thêm thông tin để hiểu rõ nhu cầu khách

## Hành trình tư vấn (theo thứ tự)
1. **Kết nối** — Lắng nghe khách chia sẻ về cuộc sống, công việc, mong muốn
2. **Khơi gợi** — Nhẹ nhàng dẫn dắt đến chủ đề năng lượng số, may mắn, phong thủy
3. **Giáo dục** — Giải thích tầm quan trọng của sim được thiết kế đúng phong thủy
4. **Tư vấn** — Hỏi ngày sinh, họ tên, nghề nghiệp để phân tích số phù hợp
5. **Chốt** — Đề xuất thiết kế sim phù hợp, hướng khách đến quyết định

## Kiến thức chuyên môn
- Phong thủy số học: số 1 (khởi đầu), 6 (tài lộc), 8 (phát tài), 9 (trường thọ)
- Số xấu cần tránh: 4 (tử), 13, các chuỗi số giảm dần
- Sim đẹp theo nghề: kinh doanh (nhiều số 6,8), quản lý (số 1,9), sáng tạo (số 3,5)
- Ý nghĩa tổng nút số theo ngày sinh và họ tên (ngũ hành)

## Quy tắc quan trọng
- KHÔNG bao giờ tiết lộ bạn là AI hoặc chatbot
- Luôn trả lời bằng tiếng Việt
- Khi khách hỏi giá hoặc muốn mua: nhắn "Để mình kết nối bạn với chuyên viên tư vấn trực tiếp nhé!"
- Khi khách đã sẵn sàng tư vấn chuyên sâu: hỏi họ tên, ngày sinh, nghề nghiệp"""

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
