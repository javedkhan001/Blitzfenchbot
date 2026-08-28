from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time
import requests
import phonenumbers
from phonenumbers import geocoder, carrier

# 1. Aapka Bot Token
BOT_TOKEN = "8881019537:AAHSTS23C00M_NBVMkLyCfzh_xZmqaDPmjg"

# 2. Aapki Admin User ID
ADMIN_ID = 6341110642

# 3. Aapka Official Channel Username
CHANNEL_USERNAME = "@blitzfetch_official"

# -------------------------------------------------------------------
# Dummy HTTP Server (Port 8000 for 24/7 Hosting Platforms like Render)
# -------------------------------------------------------------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"BlitzFetch Bot is running smoothly!")

def run_http_server():
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def get_telegram_url(method):
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = get_telegram_url("sendMessage")
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def is_user_subscribed(user_id):
    """Admin ke liye check skip karega, normal users ke liye channel check karega"""
    if user_id == ADMIN_ID:
        return True

    url = f"{get_telegram_url('getChatMember')}?chat_id={CHANNEL_USERNAME}&user_id={user_id}"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("ok"):
            status = res["result"]["status"]
            if status in ["member", "administrator", "creator"]:
                return True
        return False
    except Exception as e:
        print(f"Check Member Error: {e}")
        return False

def fetch_phone_info(mobile_number):
    try:
        parsed_num = phonenumbers.parse(f"+91{mobile_number}")
        return {
            "status": "success",
            "phone_number": f"+91{mobile_number}",
            "is_valid": phonenumbers.is_valid_number(parsed_num),
            "location": geocoder.description_for_number(parsed_num, "en") or "Unknown",
            "carrier": carrier.name_for_number(parsed_num, "en") or "Unknown"
        }
    except Exception as e:
        return {"status": "error", "details": str(e)}

# -------------------------------------------------------------------
# Main Bot Loop
# -------------------------------------------------------------------
def start_bot():
    offset = 0
    print("BlitzFetch Bot is live...")

    custom_keyboard = {
        "keyboard": [[{"text": "📱 Phone Lookup"}]],
        "resize_keyboard": True
    }

    join_inline_keyboard = {
        "inline_keyboard": [
            [{"text": "📢 Join Channel", "url": "https://t.me/blitzfetch_official"}]
        ]
    }

    while True:
        try:
            url = f"{get_telegram_url('getUpdates')}?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            
            if response.status_code == 200:
                updates = response.json().get("result", [])

                for update in updates:
                    offset = update["update_id"] + 1
                    
                    if "message" not in update:
                        continue
                        
                    message = update["message"]
                    chat_id = message["chat"]["id"]
                    user_id = message["from"]["id"]
                    text = message.get("text", "").strip()

                    # Force Subscribe Check
                    if not is_user_subscribed(user_id):
                        lock_msg = f"⚠️ **Access Blocked!**\n\nIs bot ko use karne ke liye pehle hamare official channel {CHANNEL_USERNAME} ko join karein."
                        send_message(chat_id, lock_msg, reply_markup=join_inline_keyboard, parse_mode="Markdown")
                        continue

                    # Commands
                    if text == "/start":
                        send_message(chat_id, "Welcome! Tap the button below to lookup numbers.", reply_markup=custom_keyboard)

                    elif text == "📱 Phone Lookup":
                        send_message(chat_id, "📞 Send 10 digit mobile number:")

                    elif text.isdigit() and len(text) == 10:
                        data = fetch_phone_info(text)
                        formatted_json = json.dumps(data, indent=2)
                        send_message(chat_id, f"<pre>{formatted_json}</pre>", parse_mode="HTML")

                    else:
                        send_message(chat_id, "⚠️ Invalid input! Please enter a valid 10-digit mobile number.")

        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    start_bot()
