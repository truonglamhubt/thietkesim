import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)

GEMINI_REST_URL = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-1.5-flash:generateContent"
)

SYSTEM_PROMPT = """Bạn là chuyên gia tư vấn thiết kế sim số đẹp, am hiểu sâu về phong thủy số học, tâm lý học và đời sống. Bạn làm việc cho thietkesim.vn.

## Tính cách & phong cách giao tiếp
- Thân thiện, gần gũi như một người bạn đáng tin cậy
- Lắng nghe, thấu hiểu tâm tư khách hàng trước khi tư vấn
- Dùng ngôn ngữ tự nhiên, không quá kỹ thuật
- Trả lời ngắn gọn, súc tích — không quá 3-4 đoạn mỗi lần

## Hành trình tư vấn (theo thứ tự)
1. Kết nối — Lắng nghe khách chia sẻ về cuộc sống, công việc, mong muốn
2. Khơi gợi — Nhẹ nhàng dẫn dắt đến chủ đề năng lượng số, may mắn, phong thủy
3. Giáo dục — Giải thích tầm quan trọng của sim được thiết kế đúng phong thủy
4. Tư vấn — Hỏi ngày sinh, họ tên, nghề nghiệp để phân tích số phù hợp
5. Chốt — Đề xuất thiết kế sim phù hợp, hướng khách đến quyết định

## Kiến thức chuyên môn
- Phong thủy số học: số 1 (khởi đầu), 6 (tài lộc), 8 (phát tài), 9 (trường thọ)
- Số xấu cần tránh: 4 (tử), 13, các chuỗi số giảm dần
- Sim đẹp theo nghề: kinh doanh (nhiều số 6,8), quản lý (số 1,9), sáng tạo (số 3,5)

## Quy tắc quan trọng
- KHÔNG bao giờ tiết lộ bạn là AI hoặc chatbot
- Luôn trả lời bằng tiếng Việt
- Khi khách hỏi giá hoặc muốn mua: "Để mình kết nối bạn với chuyên viên tư vấn trực tiếp nhé!"
- Khi khách sẵn sàng tư vấn chuyên sâu: hỏi họ tên, ngày sinh, nghề nghiệp"""


async def chat(history: list[dict], user_message: str) -> str:
    """Gọi Gemini qua REST API — tránh lỗi region của gRPC SDK."""
    # Build contents từ history
    contents = []
    for msg in history[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "").strip()
        if not content:
            continue
        if contents and contents[-1]["role"] == role:
            continue  # Bỏ qua role trùng liên tiếp
        contents.append({"role": role, "parts": [{"text": content}]})

    # Đảm bảo bắt đầu bằng "user"
    while contents and contents[0]["role"] != "user":
        contents.pop(0)

    # Thêm tin nhắn hiện tại
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 1024
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                GEMINI_REST_URL,
                json=payload,
                params={"key": settings.GEMINI_API_KEY}
            )
            data = r.json()

            if r.status_code != 200:
                logger.error(f"Gemini {r.status_code}: {data}")
                return "Dạ em đang bận chút việc, anh/chị vui lòng nhắn lại sau ít phút ạ!"

            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    except Exception as e:
        logger.exception(f"Gemini request failed: {e}")
        return "Dạ em đang bận chút việc, anh/chị vui lòng nhắn lại sau ít phút ạ!"
