import os
import re
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CẤU HÌNH MÔI TRƯỜNG (Anh cần nạp thêm ID các nhóm vào Render) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# ID các nhóm Telegram (Anh sẽ lấy và dán vào Environment của Render)
ID_NHOM_MAT_BAO = os.environ.get("CHAT_ID_MAT_BAO")
ID_NHOM_CHECK_SIM = os.environ.get("CHAT_ID_CHECK_SIM")
ID_NHOM_DON_CHOT = os.environ.get("CHAT_ID_DON_CHOT")

FB_PAGE_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.environ.get("FACEBOOK_VERIFY_TOKEN", "thietkesim_bi_mat_123")

# --- KỊCH BẢN CHUYÊN GIA THIẾT KẾ SIM (DẠY BOT NGỮ CẢNH) ---
KICH_BAN_CHUYEN_GIA = """
Bạn là Trợ lý AI cấp cao của anh Lâm - Chuyên gia thiết kế sim (thietkesim.vn).
PHONG CÁCH: Chuyên gia, lịch sự, thiện cảm, sâu sắc. Xưng "em", gọi khách là "anh/chị".

QUY TẮC XỬ LÝ:
1. CHÀO HỎI & TÂM LÝ: 
   - Giới thiệu là Trợ lý anh Lâm. Đóng vai chuyên gia tâm lý/bạn đồng hành để tạo thiện cảm.
   - Hỏi nhu cầu: Tìm sim theo năm sinh, tài chính, sở thích, công việc, hay phong thủy?

2. TƯ VẤN PHONG THỦY:
   - Nếu khách muốn xem số/phong thủy: Sử dụng phong thủy số học hiện đại.
   - BẮT BUỘC hỏi: Số điện thoại cần xem, Ngày tháng năm sinh, Giới tính.
   - Ăn nói linh hoạt, hướng khách tìm sim phù hợp cho mình hoặc người thân.

3. TRA CỨU & BÁO GIÁ:
   - Nếu khách hỏi sim cụ thể: Dùng dữ liệu được cấp để báo giá BÁN.
   - Nếu chưa có dữ liệu: Lịch sự bảo khách đợi em check tình trạng kho và sẽ báo lại ngay.
   - TUYỆT ĐỐI không lộ giá gốc/tên thợ. Ví dụ: "Dạ số 09xx bên em đang có giá rất tốt là..."
   - Nếu tìm sim theo yêu cầu: Đưa ra 5 lựa chọn từ thấp đến cao (giả lập hoặc từ web thietkesim.vn).

4. XỬ LÝ CHỐT ĐƠN & MẶC CẢ:
   - Khách ưng sim: Chúc mừng khách và xin số điện thoại/Zalo để anh Lâm làm thủ tục.
   - Khách mặc cả: Giải thích giá trị của sim (phong thủy, độ hiếm, thương hiệu). 
   - Nếu khách vẫn muốn giảm: Bảo để em xin ý kiến anh Lâm lấy giá ưu đãi nhất cho khách và xin số liên hệ.

5. MỤC TIÊU CUỐI: Luôn xin được số Zalo/SĐT để anh Lâm trực tiếp chốt deal.
"""

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=KICH_BAN_CHUYEN_GIA
)

def gui_telegram(chat_id, noidung):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": noidung})

def gui_facebook(sender_id, noidung):
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={FB_PAGE_TOKEN}"
    requests.post(url, json={"recipient": {"id": sender_id}, "message": {"text": noidung}})

# --- LOGIC PHÂN LOẠI ĐỂ ĐẨY VỀ CÁC NHÓM TELEGRAM ---
def phan_loai_va_bao_cao(tin_nhan_khach, ai_tra_loi):
    txt = tin_nhan_khach.lower()
    
    # 1. Nhóm Đơn Chốt (Khi khách ưng, chốt, hoặc mặc cả cần sếp can thiệp)
    if any(w in txt for w in ['mua', 'lấy', 'chốt', 'giảm giá', 'bớt', 'rẻ hơn', 'ưng']):
        thong_bao = f"💰 ĐƠN CẦN CHỐT:\n- Khách nhắn: {tin_nhan_khach}\n- AI đang lái: {ai_tra_loi}"
        gui_telegram(ID_NHOM_DON_CHOT, thong_bao)
    
    # 2. Nhóm Check SIM (Khi khách hỏi số cụ thể)
    elif bool(re.search(r'\d{4,}', txt)) or "check" in txt:
        thong_bao = f"🔍 CHECK SIM GIÚP EM:\n- Khách hỏi: {tin_nhan_khach}"
        gui_telegram(ID_NHOM_CHECK_SIM, thong_bao)
    
    # 3. Nhóm Mật Báo chung (Theo dõi mọi cuộc hội thoại)
    else:
        gui_telegram(ID_NHOM_MAT_BAO, f"💬 KHÁCH CHAT: {tin_nhan_khach}")

@app.route('/webhook', methods=['GET', 'POST'])
def fb_webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == FB_VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        return 'Sai mã', 403
    
    body = request.json
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event and "text" in event["message"]:
                    sender_id = event["sender"]["id"]
                    msg_text = event["message"]["text"]
                    
                    # AI soạn câu trả lời dựa trên kịch bản chuyên gia
                    response = model.generate_content(msg_text)
                    ai_reply = response.text
                    
                    # Gửi trả lời khách trên Facebook
                    gui_facebook(sender_id, ai_reply)
                    
                    # Phân loại để báo về đúng nhóm Telegram
                    phan_loai_va_bao_cao(msg_text, ai_reply)
                    
    return "OK", 200

@app.route('/')
def home(): return "Bot Chuyên Gia Thietkesim v3.0 Live!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
