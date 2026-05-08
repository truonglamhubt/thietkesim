import os
import re
import requests
import google.generativeai as genai
from flask import Flask, request
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv() # Tải các biến từ file .env
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)

app = Flask(__name__)

# 1. LẤY MÃ BẢO MẬT
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ID_MAT_BAO = os.environ.get("CHAT_ID_MAT_BAO")
ID_CHECK_SIM = os.environ.get("CHAT_ID_CHECK_SIM")
ID_DON_CHOT = os.environ.get("CHAT_ID_DON_CHOT")
FB_TOKEN = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN")
FB_VERIFY = os.environ.get("FACEBOOK_VERIFY_TOKEN", "thietkesim_bi_mat_123")

# 2. KHỞI TẠO AI (DÙNG BẢN LATEST)
try:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", 
        system_instruction="Bạn là trợ lý anh Lâm thietkesim.vn. Trả lời lịch sự, chuyên nghiệp, xưng em gọi anh/chị. Tuyệt đối không để lộ giá gốc."
    )
    print("✅ AI ĐÃ SẴN SÀNG!")
except Exception as e:
    print(f"❌ LỖI KHỞI TẠO AI: {e}")

def send_tg(chat_id, text):
    if not chat_id: return
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": text})

def send_fb(sender_id, text):
    requests.post(f"https://graph.facebook.com/v21.0/me/messages?access_token={FB_TOKEN}", json={"recipient": {"id": sender_id}, "message": {"text": text}})

# 3. LUỒNG XỬ LÝ CHÍNH
def process_chat(msg, platform="FB"):
    try:
        # Gọi Gemini xử lý
        response = model.generate_content(msg)
        reply = response.text
        
        # Phân loại báo cáo Telegram
        txt = msg.lower()
        if any(w in txt for w in ['mua', 'chốt', 'giảm', 'bớt', 'giá']):
            send_tg(ID_DON_CHOT, f"💰 ĐƠN ({platform}): {msg}\nAI: {reply}")
        elif bool(re.search(r'\d{4,}', txt)):
            send_tg(ID_CHECK_SIM, f"🔍 CHECK ({platform}): {msg}")
        else:
            send_tg(ID_MAT_BAO, f"💬 CHAT ({platform}): {msg}")
        return reply
    except Exception as e:
        # IN LỖI RA LOGS ĐỂ SẾP LÂM KIỂM TRA
        print(f"❌ LỖI AI KHÔNG TRẢ LỜI ĐƯỢC: {e}")
        return "Dạ em đang bận chút, anh Lâm sẽ gọi lại anh ngay ạ!"

@app.route('/webhook', methods=['GET', 'POST'])
def fb_webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == FB_VERIFY: return request.args.get('hub.challenge'), 200
        return 'Error', 403
    body = request.json
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event and "text" in event["message"]:
                    reply = process_chat(event["message"]["text"], "FB")
                    send_fb(event["sender"]["id"], reply)
    return "OK", 200

@app.route('/telegram', methods=['POST'])
def tg_webhook():
    data = request.json
    if "message" in data and "text" in data["message"]:
        cid = data["message"]["chat"]["id"]
        # Chỉ trả lời nếu không phải tin nhắn trong các nhóm quản lý
        if str(cid) not in [str(ID_MAT_BAO), str(ID_CHECK_SIM), str(ID_DON_CHOT)]:
            reply = process_chat(data["message"]["text"], "TG")
            send_tg(cid, reply)
    return "OK", 200

@app.route('/')
def home(): return "Bot Thietkesim v4.0 is Live!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
