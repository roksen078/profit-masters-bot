import os
import re
import json
import time
import shutil
import logging
from threading import Thread
from datetime import datetime
import telebot
from telebot import types
from flask import Flask

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- FLASK KEEP ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 System Operational: Profit Masters V3 Core Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    server = Thread(target=run_flask)
    server.daemon = True
    server.start()

# --- BOT SETUP & DB ENGINE ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID_ENV = os.environ.get("ADMIN_ID", "6191773010")

try:
    if "," in ADMIN_ID_ENV:
        ADMINS = [int(x.strip()) for x in ADMIN_ID_ENV.split(",") if x.strip().isdigit()]
    else:
        ADMINS = [int(ADMIN_ID_ENV)] if ADMIN_ID_ENV.isdigit() else [6191773010]
except Exception:
    ADMINS = [6191773010]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
BACKUP_FILE = os.path.join(DATA_DIR, "config_backup.json")

# EXACT DATA MATCHING THE PROVIDED SCREENSHOTS
EXACT_WELCOME_TEXT = (
    "🎉 <b>Join Official Big Promo Code Channel</b>\n\n"
    "📅 <b>Daily FREE BIG CODE</b>\n\n"
    "👇 <b>Join our channels below and claim your code!</b>"
)

DEFAULT_SETTINGS = {
    "admins": ADMINS,
    "maintenance": False,
    "welcome_photo": "https://graph.org/file/f6e7c7a523ab65cb6fcd9.jpg", 
    "welcome_caption": EXACT_WELCOME_TEXT,
    "free_code_text": "🎁 MASTER-PROFIT-CODE-2026-X79",
    "verification_btn_text": "🎁 Get My Free Code", 
    "broadcast_btn_text": "👉 Register Now",  
    "channels": ["@channel1", "@channel2", "@channel3", "@channel4"], 
    "buttons": [
        {"text": "🚀 Claim ₹500", "type": "url", "value": "https://t.me/telegram"},
        {"text": "🎁 Unlock Code", "type": "url", "value": "https://t.me/telegram"},
        {"text": "🎯 Claim bonus", "type": "url", "value": "https://t.me/telegram"},
        {"text": "💎 VIP GIFT", "type": "url", "value": "https://t.me/telegram"}
    ],
    "users": {}, 
    "clicks": {
        "total": 0,
        "button_wise": {
            "🚀 Claim ₹500": 0,
            "🎁 Unlock Code": 0,
            "🎯 Claim bonus": 0,
            "💎 VIP GIFT": 0,
            "verification_button_click": 0,
            "dynamic_broadcast_link": 0
        }
    }
}

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_db():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4, ensure_ascii=False)
        return DEFAULT_SETTINGS
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        if os.path.exists(BACKUP_FILE):
            try:
                shutil.copy(BACKUP_FILE, CONFIG_FILE)
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_SETTINGS

def save_db(data):
    try:
        if os.path.exists(CONFIG_FILE):
            shutil.copy(CONFIG_FILE, BACKUP_FILE)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Save error: {e}")

db = load_db()

for adm in ADMINS:
    if adm not in db["admins"]:
        db["admins"].append(adm)
save_db(db)

# --- MIDDLEWARES & UTILS ---
def is_admin(user_id):
    return int(user_id) in db["admins"]

def check_force_join(user_id):
    if not db["channels"]:
        return True
    for ch in db["channels"]:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

def record_click(button_name, user_id=None):
    db["clicks"]["total"] += 1
    db["clicks"]["button_wise"][button_name] = db["clicks"]["button_wise"].get(button_name, 0) + 1
    if user_id and str(user_id) in db["users"]:
        db["users"][str(user_id)]["clicks"] = db["users"][str(user_id)].get("clicks", 0) + 1
    save_db(db)

def extract_first_link(text):
    if not text:
        return None
    urls = re.findall(r'(https?://[^\s]+)', text)
    return urls[0] if urls else None

def generate_welcome_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    grid_buttons = []
    
    for btn in db["buttons"]:
        if btn["type"] == "url":
            grid_buttons.append(types.InlineKeyboardButton(text=btn["text"], url=btn["value"]))
        else:
            grid_buttons.append(types.InlineKeyboardButton(text=btn["text"], callback_data=btn["value"]))
            
    markup.add(*grid_buttons)
    
    v_text = db.get("verification_btn_text", "🎁 Get My Free Code")
    markup.row(types.InlineKeyboardButton(text=v_text, callback_data="get_code"))
    return markup

def system_check(func):
    def wrapper(message):
        user_id = str(message.from_user.id)
        if user_id not in db["users"]:
            db["users"][user_id] = {"joined": time.time(), "clicks": 0, "banned": False, "last_pin_id": None}
            save_db(db)
        if db["users"][user_id].get("banned", False):
            return
        if db.get("maintenance", False) and not is_admin(user_id):
            bot.send_message(message.chat.id, "⚠️ <b>System Alert:</b> Under technical construction.")
            return
        return func(message)
    return wrapper

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
@system_check
def start_handler(message):
    try:
        bot.send_photo(
            message.chat.id,
            photo=db["welcome_photo"],
            caption=db["welcome_caption"],
            reply_markup=generate_welcome_keyboard()
        )
    except Exception:
        bot.send_message(message.chat.id, db["welcome_caption"], reply_markup=generate_welcome_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def query_router(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if call.data == "get_code":
        record_click("verification_button_click", user_id)
        bot.answer_callback_query(call.id, "🔐 Verifying membership protocols...")
        
        prog_msg = bot.send_message(
            chat_id, 
            "⏳ <b>Verification in Progress...</b>\n\n"
            "🔍 <b>Checking if you pinned all 4 channels...</b>\n\n"
            "⏱️ <b>Please wait 5 seconds...</b>"
        )
        
        time.sleep(5.0)
        try:
            bot.delete_message(chat_id, prog_msg.message_id)
        except Exception: pass
            
        if check_force_join(user_id):
            success_txt = (
                f"🎉 <b>Verification Successful!</b>\n\n"
                f"🎁 Your allocation code: <code>{db['free_code_text']}</code>"
            )
            bot.send_message(chat_id, success_txt)
        else:
            error_txt = (
                "⚠️ <b>Aapne Join Nahi Kiya!</b>\n\n"
                "Kripaya upar diye gaye 4 channels join karein.\n\n"
                "📌 <b>Zaruri:</b> 4 channels ko Pin karke rakho, tabhi code milega!"
            )
            bot.send_message(chat_id, error_txt)
        return

    if call.data == "dynamic_broadcast_click":
        record_click("dynamic_broadcast_link", user_id)
        bot.answer_callback_query(call.id, "Redirecting to your destination...")
        return

    if call.data.startswith("del_btn_"):
        if not is_admin(user_id): return
        btn_index = int(call.data.split("_")[2])
        try:
            removed_btn = db["buttons"].pop(btn_index)
            save_db(db)
            bot.edit_message_text(f"✅ Button <b>{removed_btn['text']}</b> permanently deleted!", chat_id, call.message.message_id)
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ Error: {e}", show_alert=True)
        return

    if call.data.startswith("edit_name_"):
        if not is_admin(user_id): return
        btn_index = int(call.data.split("_")[2])
        admin_states[user_id] = f"edit_btn_name_process_{btn_index}"
        bot.send_message(chat_id, f"📥 Send me the new name/text for button <b>{db['buttons'][btn_index]['text']}</b>:")
        bot.answer_callback_query(call.id)
        return

    if call.data.startswith("edit_link_"):
        if not is_admin(user_id): return
        btn_index = int(call.data.split("_")[2])
        admin_states[user_id] = f"edit_btn_link_process_{btn_index}"
        bot.send_message(chat_id, f"📥 Send me the new URL/Link for button <b>{db['buttons'][btn_index]['text']}</b>:")
        bot.answer_callback_query(call.id)
        return

# --- PRIVATE ADMIN MATRIX LAYER ---
admin_states = {}

@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if not is_admin(message.from_user.id): return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row("📊 Analytics & Stats", "⚙️ Default Configuration Settings")
    markup.row("⏩ Forward Broadcast", "📝 Copy Broadcast")
    markup.row("📸 Change Photo", "✍️ Change Caption")
    markup.row("➕ Add Welcome Button", "✏️ Edit Button Text")
    markup.row("🔗 Edit Button URL", "➖ Remove Welcome Button")
    markup.row("✏️ Edit Free Code Btn Text", "✏️ Broadcast Button Text")
    markup.row("🔗 Update Channels", "🎚️ Maintenance Mode")
    markup.row("🔄 Reset URL Click Counter", "")
    
    bot.send_message(message.chat.id, "👨‍💼 <b>System Control Center Node Activated:</b>", reply_markup=markup)

@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id), content_types=['text', 'photo', 'video', 'document', 'voice'])
def handle_admin_inputs(message):
    user_id = message.from_user.id
    text = message.text if message.content_type == 'text' else ""
    
    if text == "📊 Analytics & Stats":
        total_u = len(db["users"])
        total_cl = db
