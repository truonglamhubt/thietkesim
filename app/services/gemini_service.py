import asyncio
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


def _build_full_prompt(history: list[dict], user_message: str) -> str:
    """Ghép history + tin nhắn mới thành 1 prompt hoàn chỉnh."""
    prompt = f"{SYSTEM_PROMPT}\n\n"
    if history:
        history_lines = []
        for msg in history[-10:]:  # Lấy 10 tin gần nhất
            role_label = "Khách" if msg.get("role") == "user" else "Tư vấn viên"
            history_lines.append(f"{role_label}: {msg.get('content', '')}")
        prompt += "LỊCH SỬ HỘI THOẠI:\n" + "\n".join(history_lines) + "\n\n"
    prompt += f"KHÁCH NHẮN: {user_message}\nTƯ VẤN VIÊN TRẢ LỜI:"
    return prompt


def _fetch_gemini_reply(full_prompt: str) -> str:
    """Gọi Gemini API (sync) — tự động chọn model khả dụng."""
    try:
        # Lấy danh sách model API key này được phép dùng
        allowed = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]
        if not allowed:
            return "Dạ em đang bận chút việc, anh/chị vui lòng nhắn lại sau ít phút ạ!"

        # Ưu tiên flash → 1.5 → các model khác
        allowed.sort(key=lambda x: (
            0 if "flash" in x else 1,
            0 if "1.5" in x else 1
        ))

        last_error = ""
        for model_name in allowed:
            try:
                model = genai.GenerativeModel(model_name)
                config = genai.types.GenerationConfig(temperature=0.8)
                response = model.generate_content(full_prompt, generation_config=config)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                last_error = str(e)
                continue

        logger.error(f"Tất cả model thất bại. Lỗi cuối: {last_error}")
        return "Dạ em đang bận chút việc, anh/chị vui lòng nhắn lại sau ít phút ạ!"

    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Dạ em đang bận chút việc, anh/chị vui lòng nhắn lại sau ít phút ạ!"


async def chat(history: list[dict], user_message: str) -> str:
    """Gửi tin nhắn tới Gemini kèm lịch sử hội thoại."""
    full_prompt = _build_full_prompt(history, user_message)
    # Chạy sync Gemini trong thread riêng để không block FastAPI
    return await asyncio.to_thread(_fetch_gemini_reply, full_prompt)
