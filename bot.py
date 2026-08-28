from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import threading
import time
import requests
import phonenumbers
from phonenumbers import geocoder, carrier

# 1. Aapka Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8881019537:AAHSTS23C...") # Yahan apna token check kar lena

# 2. Aapki Admin User ID (Yahan aap koi bhi valid Telegram User ID daal sakte hain)
ADMIN_ID = 6341110642

# 3. Aapka Official Channel Username
CHANNEL_USERNAME = "@blitzfetch_official"

# ----------------------------------------------------
# Dynamic Port HTTP Server for Render
# ----------------------------------------------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"BlitzFetch Bot is running smoothly!")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()

# ----------------------------------------------------
# Helper Functions
# ----------------------------------------------------
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
            "location": geocoder.description_for_number(parsed_num, "en"),
            "carrier": carrier.name_for_number(parsed_num, "en")
        }
    except Exception as e:
        return {"status": "error", "details": str(e)}

# ----------------------------------------------------
# Main Bot Loop
# ----------------------------------------------------
def start_bot():
    offset = 0
    print("BlitzFetch Bot is live...")
    
    custom_keyboard = {
        "keyboard": [[{"text": "📱 Phone Lookup"}]],
        "resize_keyboard": True
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
                        lock_msg = f"⚠️ **Access Blocked!**\n\nPlease join our official channel {CHANNEL_USERNAME} to use this bot."
                        send_message(chat_id, lock_msg)
                        continue
                    
                    # Commands
                    if text == "/start":
                        send_message(chat_id, "Welcome to BlitzFetch Bot! Choose an option below:", reply_markup=custom_keyboard)
                        
                    elif text == "📱 Phone Lookup":
                        send_message(chat_id, "Send me a 10-digit mobile number to lookup:")
                        
                    elif text.isdigit() and len(text) == 10:
                        data = fetch_phone_info(text)
                        formatted_json = json.dumps(data, indent=4)
                        send_message(chat_id, f"<pre>{formatted_json}</pre>", parse_mode="HTML")
                        
                    else:
                        send_message(chat_id, "⚠️ Invalid command or phone number. Please use the keyboard options.")
                        
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    threading.Thread(target=start_bot, daemon=True).start()
    run_http_server()
