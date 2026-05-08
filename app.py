import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# 1. LẤY CẤU HÌNH TỪ SERVER RENDER (Tuyệt đối bảo mật)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID_MAT_BAO = os.environ.get("CHAT_ID_MAT_BAO")

# 2. KHỞI TẠO BỘ NÃO GEMINI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction="""Bạn là Trợ lý AI kiêm Chuyên gia tư vấn SIM số đẹp của thietkesim.vn.
    Nhiệm vụ: Dựa vào danh sách SIM, báo giá cho khách. 
    Tuyệt đối không tiết lộ Giá gốc và Thông tin thợ.
    Luôn chốt lại bằng việc xin số điện thoại/Zalo."""
)

def gui_telegram_mat_bao(noidung):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID_MAT_BAO, "text": noidung}
    requests.post(url, json=payload)

# 3. API ĐỂ NHẬN YÊU CẦU
@app.route('/chat', methods=['POST'])
def chat_voi_bot():
    data = request.json
    yeu_cau_cua_khach = data.get("tin_nhan", "")
    
    # Giả lập dữ liệu tìm được (Sau này sẽ nối với code lấy từ web thực tế)
    danh_sach_sim_tim_duoc = [
        {"so": "0923.61.6868", "gia_ban": "52.000.000đ", "gia_goc": "45tr", "tho": "A.Hải - 09xx"},
        {"so": "0993.63.6868", "gia_ban": "120.000.000đ", "gia_goc": "100tr", "tho": "C.Lan - 08xx"}
    ]
    
    # Gửi Telegram cho sếp
    tin_mat_bao = "🚨 CÓ KHÁCH ĐANG TÌM SIM:\n"
    for sim in danh_sach_sim_tim_duoc:
        tin_mat_bao += f"- Số: {sim['so']} | Bán: {sim['gia_ban']} | Gốc: {sim['gia_goc']} | Thợ: {sim['tho']}\n"
    gui_telegram_mat_bao(tin_mat_bao)

    # Gemini trả lời khách
    du_lieu_cho_gemini = "Danh sách sim:\n" + "\n".join([f"- Số: {s['so']}, Giá: {s['gia_ban']}" for s in danh_sach_sim_tim_duoc])
    prompt = f"Khách hỏi: '{yeu_cau_cua_khach}'. Dữ liệu: {du_lieu_cho_gemini}."
    
    response = model.generate_content(prompt)
    
    return jsonify({"bot_tra_loi": response.text})

@app.route('/', methods=['GET'])
def home():
    return "Hệ thống Bot Thietkesim.vn đang hoạt động 24/7!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)