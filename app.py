import os
import re
import requests
import google.generativeai as genai
from flask import Flask, request

app = Flask(__name__)

# --- 1. LẤY CẤU HÌNH BẢO MẬT ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

ID_NHOM_MAT_BAO = os.environ.get("CHAT_ID_MAT_BAO")
ID_NHOM_CHECK_SIM = os.environ.get("CHAT_ID_CHECK_SIM")
ID_NHOM_DON_CHOT = os.environ.get("CHAT_ID_DON_CHOT")

FB_PAGE_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.environ.get("FACEBOOK_VERIFY_TOKEN", "thietkesim_bi_mat_123")

# --- 2. KỊCH BẢN CHUYÊN GIA ---
KICH_BAN_CHUYEN_GIA = """
Bạn là Trợ lý AI cấp cao của anh Lâm - Chuyên gia thiết kế sim (thietkesim.vn).
PHONG CÁCH: Chuyên gia, lịch sự, thiện cảm, sâu sắc. Xưng "em", gọi khách là "anh/chị".

QUY TẮC XỬ LÝ:
1. CHÀO HỎI: Giới thiệu là Trợ lý anh Lâm. Hỏi nhu cầu: Tìm sim theo năm sinh, tài chính, sở thích, công việc, hay phong thủy?
2. PHONG THỦY: Nếu khách nhờ xem số, yêu cầu: Số điện thoại, Ngày sinh, Giới tính. Tư vấn dựa trên phong thủy số học hiện đại.
3. TRA CỨU: Nếu khách hỏi sim cụ thể, báo giá Bán. TUYỆT ĐỐI không lộ giá gốc/tên thợ. Nếu chưa rõ giá, bảo khách đợi em check kho và báo lại ngay.
4. CHỐT ĐƠN: Khách ưng hoặc mặc cả -> Giải thích giá trị sim, xin SĐT/Zalo để anh Lâm hỗ trợ giá tốt nhất.
5. MỤC TIÊU: Luôn xin được số Zalo/SĐT để anh Lâm trực tiếp chốt deal.
"""

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=KICH_BAN_CHUYEN_GIA
)

# --- 3. CÁC HÀM GỬI TIN NHẮN ---
def send_telegram(chat_id, text):
    if not chat_id: return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_facebook(sender_id, text):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={FB_PAGE_TOKEN}"
    requests.post(url, json={"recipient": {"id": sender_id}, "message": {"text": text}})

# --- 4. LOGIC XỬ LÝ VÀ PHÂN LOẠI ---
def handle_ai_logic(msg_text, platform="Facebook"):
    # AI soạn câu trả lời
    response = model.generate_content(msg_text)
    ai_reply = response.text
    
    # Phân loại để báo cáo về Telegram
    txt = msg_text.lower()
    if any(w in txt for w in ['mua', 'lấy', 'chốt', 'giảm giá', 'bớt', 'rẻ hơn', 'ưng']):
        thong_bao = f"💰 ĐƠN CẦN CHỐT ({platform}):\n- Khách: {msg_text}\n- AI đang lái: {ai_reply}"
        send_telegram(ID_NHOM_DON_CHOT, thong_bao)
    elif bool(re.search(r'\d{4,}', txt)) or "check" in txt:
        thong_bao = f"🔍 CHECK SIM ({platform}):\n- Khách hỏi: {msg_text}"
        send_telegram(ID_NHOM_CHECK_SIM, thong_bao)
    else:
        send_telegram(ID_NHOM_MAT_BAO, f"💬 KHÁCH CHAT ({platform}): {msg_text}")
    
    return ai_reply

# --- 5. CỔNG KẾT NỐI (ROUTES) ---
@app.route('/webhook', methods=['GET', 'POST'])
def fb_webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == FB_VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        return 'Wrong token', 403
    
    body = request.json
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event and "text" in event["message"]:
                    sid = event["sender"]["id"]
                    msg = event["message"]["text"]
                    reply = handle_ai_logic(msg, "Facebook")
                    send_facebook(sid, reply)
    return "OK", 200

@app.route('/telegram', methods=['POST'])
def tg_webhook():
    data = request.json
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        # Không trả lời tin nhắn trong các nhóm quản lý
        if str(chat_id) not in [str(ID_NHOM_MAT_BAO), str(ID_NHOM_CHECK_SIM), str(ID_NHOM_DON_CHOT)]:
            msg = data["message"]["text"]
            reply = handle_ai_logic(msg, "Telegram")
            send_telegram(chat_id, reply)
    return "OK", 200

@app.route('/')
def home():
    return "Bot Chuyên Gia Thietkesim v3.0 is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
