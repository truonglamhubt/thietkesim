import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- 1. LẤY CẤU HÌNH BẢO MẬT TỪ RENDER ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID_MAT_BAO = os.environ.get("CHAT_ID_MAT_BAO")

# [MỚI] Chìa khóa Facebook
FB_PAGE_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.environ.get("FACEBOOK_VERIFY_TOKEN", "thietkesim_bi_mat_123")

# --- 2. KHỞI TẠO BỘ NÃO GEMINI ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    system_instruction="""Bạn là Trợ lý AI kiêm Chuyên gia tư vấn SIM số đẹp của thietkesim.vn.
    Giọng điệu: Thân thiện, chuyên nghiệp, luôn xưng "em" và gọi khách là "anh/chị". 
    Nhiệm vụ: Dựa vào dữ liệu hệ thống cấp, báo giá cho khách. 
    TUYỆT ĐỐI không tiết lộ Giá gốc và Tên thợ.
    Luôn kết thúc bằng việc xin số điện thoại/Zalo để tư vấn chi tiết."""
)

def gui_telegram_mat_bao(noidung):
    """Bắn tin nhắn mật báo về Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID_MAT_BAO, "text": noidung}
    requests.post(url, json=payload)

def gui_tin_nhan_facebook(sender_id, text):
    """Gửi tin nhắn trả lời khách trên Messenger"""
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={FB_PAGE_TOKEN}"
    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": text}
    }
    requests.post(url, json=payload)

# --- 3. ĐƯỜNG CÁP KẾT NỐI VỚI FACEBOOK (WEBHOOK) ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # 3.1. Facebook kiểm tra đường truyền (Lần đầu cắm cáp)
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode and token:
            if mode == 'subscribe' and token == FB_VERIFY_TOKEN:
                return challenge, 200
            else:
                return 'Sai mã xác minh', 403
        return 'Webhook đang hoạt động', 200

    # 3.2. Khách hàng nhắn tin trên Messenger
    elif request.method == 'POST':
        body = request.json
        if body.get("object") == "page":
            for entry in body.get("entry", []):
                for webhook_event in entry.get("messaging", []):
                    # Nếu có tin nhắn văn bản gửi tới
                    if "message" in webhook_event and "text" in webhook_event["message"]:
                        sender_id = webhook_event["sender"]["id"]
                        tin_nhan_khach = webhook_event["message"]["text"]
                        
                        # --- KỊCH BẢN 2 BƯỚC KÉP ---
                        # (Mô phỏng dữ liệu web cào được)
                        danh_sach_sim_tim_duoc = [
                            {"so": "0923.61.6868", "gia_ban": "52.000.000đ", "gia_goc": "45tr", "tho": "A.Hải - 09xx"},
                            {"so": "0993.63.6868", "gia_ban": "120.000.000đ", "gia_goc": "100tr", "tho": "C.Lan - 08xx"}
                        ]
                        
                        # Bước A: Mật báo Telegram cho Sếp Lâm
                        tin_mat_bao = f"🚨 CÓ KHÁCH HỎI TRÊN MESSENGER: '{tin_nhan_khach}'\n"
                        for sim in danh_sach_sim_tim_duoc:
                            tin_mat_bao += f"- Số: {sim['so']} | Bán: {sim['gia_ban']} | Gốc: {sim['gia_goc']} | Thợ: {sim['tho']}\n"
                        gui_telegram_mat_bao(tin_mat_bao)
                        
                        # Bước B: AI soạn văn bản trả lời khách
                        du_lieu_cho_gemini = "Danh sách sim:\n" + "\n".join([f"- Số: {s['so']}, Giá: {s['gia_ban']}" for s in danh_sach_sim_tim_duoc])
                        prompt = f"Khách hỏi: '{tin_nhan_khach}'. Dữ liệu: {du_lieu_cho_gemini}."
                        response = model.generate_content(prompt)
                        
                        # Bước C: Trả lời lại ngay trên Messenger
                        gui_tin_nhan_facebook(sender_id, response.text)
                        
        return 'OK', 200

@app.route('/', methods=['GET'])
def home():
    return "Hệ thống Bot Thietkesim.vn đang hoạt động 24/7!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
