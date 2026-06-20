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
    "users": {}, # {"user_id": {"joined": timestamp, "clicks": 0, "banned": False, "last_pin_id": message_id}}
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
        total_cl = db["clicks"]["total"]
        breakdown = ""
        for k, v in db["clicks"]["button_wise"].items():
            breakdown += f" 🔹 <i>{k}:</i> <code>{v}</code>\n"
            
        stats_msg = (
            f"📊 <b>System Infrastructure Metrics:</b>\n\n"
            f"👥 Total Registered Base Users: <code>{total_u}</code>\n"
            f"🎯 Total Interaction Clicks: <code>{total_cl}</code>\n\n"
            f"📈 <b>Button Tracking Analytics Grid:</b>\n{breakdown}"
        )
        bot.send_message(message.chat.id, stats_msg)
        return
        
    if text == "🎚️ Maintenance Mode":
        db["maintenance"] = not db.get("maintenance", False)
        save_db(db)
        state = "ENABLED 🛑" if db["maintenance"] else "DISABLED 🟢"
        bot.send_message(message.chat.id, f"✅ Maintenance Mode is now {state}")
        return

    if text == "📸 Change Photo":
        admin_states[user_id] = "awaiting_photo"
        bot.send_message(message.chat.id, "📥 Send me the raw photo file or direct URL image path:")
        return

    if text == "✍️ Change Caption":
        admin_states[user_id] = "awaiting_caption"
        bot.send_message(message.chat.id, "📥 Send me the raw formatting text schema block:")
        return

    if text == "✏️ Edit Free Code Btn Text":
        admin_states[user_id] = "awaiting_verification_btn_text"
        bot.send_message(message.chat.id, f"📥 Current Text: <code>{db.get('verification_btn_text', '🎁 Get My Free Code')}</code>\nSend me the new text for the main verification button:")
        return

    if text == "✏️ Broadcast Button Text":
        admin_states[user_id] = "awaiting_broadcast_btn_text"
        bot.send_message(message.chat.id, f"📥 Current Text: <code>{db.get('broadcast_btn_text', '👉 Register Now')}</code>\nSend me the new name for the auto-extract link button:")
        return
        
    if text == "🔗 Update Channels":
        admin_states[user_id] = "awaiting_channels"
        bot.send_message(message.chat.id, "📥 Send channels separated by space (e.g. <code>@ch1 @ch2 @ch3 @ch4</code>):")
        return

    if text == "➕ Add Welcome Button":
        admin_states[user_id] = "add_btn_name"
        bot.send_message(message.chat.id, "📥 Enter the text/name for the new button (e.g., <code>🔥 Join VIP</code>):")
        return

    if text == "✏️ Edit Button Text":
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_buttons = False
        for idx, btn in enumerate(db["buttons"]):
            markup.add(types.InlineKeyboardButton(text=f"✏️ {btn['text']}", callback_data=f"edit_name_{idx}"))
            has_buttons = True
        if has_buttons:
            bot.send_message(message.chat.id, "📝 Select the button you want to rename:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "ℹ️ No custom buttons found to edit.")
        return

    if text == "🔗 Edit Button URL":
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_buttons = False
        for idx, btn in enumerate(db["buttons"]):
            markup.add(types.InlineKeyboardButton(text=f"🔗 {btn['text']}", callback_data=f"edit_link_{idx}"))
            has_buttons = True
        if has_buttons:
            bot.send_message(message.chat.id, "🔗 Select the button whose URL link you want to change:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "ℹ️ No custom buttons found to edit.")
        return

    if text == "➖ Remove Welcome Button":
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_buttons = False
        for idx, btn in enumerate(db["buttons"]):
            markup.add(types.InlineKeyboardButton(text=f"❌ {btn['text']}", callback_data=f"del_btn_{idx}"))
            has_buttons = True
        if has_buttons:
            bot.send_message(message.chat.id, "🗑️ Select the button you want to remove permanently:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "ℹ️ No custom URL buttons found to delete.")
        return

    if text in ["⏩ Forward Broadcast", "📝 Copy Broadcast"]:
        admin_states[user_id] = f"broadcast_{'forward' if 'Forward' in text else 'copy'}"
        bot.send_message(message.chat.id, f"📥 Send or forward any message/post now. Bot will auto-extract link, attach custom button, and handle AUTO-PIN sequence! [Mode: {admin_states[user_id].upper()}]:")
        return
        
    if text == "🔄 Reset URL Click Counter":
        db["clicks"]["button_wise"]["dynamic_broadcast_link"] = 0
        save_db(db)
        bot.send_message(message.chat.id, "✅ URL Click counter has been reset to 0.")
        return

    if text == "⚙️ Default Configuration Settings":
        db["welcome_photo"] = DEFAULT_SETTINGS["welcome_photo"]
        db["welcome_caption"] = DEFAULT_SETTINGS["welcome_caption"]
        db["buttons"] = DEFAULT_SETTINGS["buttons"]
        db["broadcast_btn_text"] = DEFAULT_SETTINGS["broadcast_btn_text"]
        db["verification_btn_text"] = DEFAULT_SETTINGS["verification_btn_text"]
        db["clicks"]["total"] = 0
        db["clicks"]["button_wise"] = {b["text"]: 0 for b in DEFAULT_SETTINGS["buttons"]}
        db["clicks"]["button_wise"]["verification_button_click"] = 0
        db["clicks"]["button_wise"]["dynamic_broadcast_link"] = 0
        save_db(db)
        bot.send_message(message.chat.id, "🔄 <b>Default Settings Restored Successfully!</b>")
        return

    # Process pending states
    state = admin_states.get(user_id)
    if not state: return
    
    if state == "awaiting_photo":
        if message.content_type == 'photo':
            db["welcome_photo"] = message.photo[-1].file_id
        else:
            db["welcome_photo"] = message.text
        save_db(db)
        bot.send_message(message.chat.id, "✅ Welcome Photo customized successfully!")
        admin_states.pop(user_id, None)
        
    elif state == "awaiting_caption":
        db["welcome_caption"] = message.text
        save_db(db)
        bot.send_message(message.chat.id, "✅ Caption Schema applied successfully!")
        admin_states.pop(user_id, None)

    elif state == "add_btn_name":
        if message.content_type == 'text':
            admin_states[user_id] = f"add_btn_url_{message.text.strip()}"
            bot.send_message(message.chat.id, f"📥 Now send the full URL/Link for <b>{message.text.strip()}</b>:")
        else: admin_states.pop(user_id, None)

    elif state.startswith("add_btn_url_"):
        btn_name = state.replace("add_btn_url_", "")
        admin_states.pop(user_id, None)
        if message.content_type == 'text' and (message.text.startswith("http://") or message.text.startswith("https://")):
            db["buttons"].append({"text": btn_name, "type": "url", "value": message.text.strip()})
            db["clicks"]["button_wise"][btn_name] = 0
            save_db(db)
            bot.send_message(message.chat.id, f"✅ New welcome button <b>{btn_name}</b> added successfully!")
        else: bot.send_message(message.chat.id, "❌ Invalid Link! Cancelled.")

    elif state.startswith("edit_btn_name_process_"):
        btn_idx = int(state.split("_")[-1])
        admin_states.pop(user_id, None)
        if message.content_type == 'text':
            old_name = db["buttons"][btn_idx]["text"]
            new_name = message.text.strip()
            db["buttons"][btn_idx]["text"] = new_name
            if old_name in db["clicks"]["button_wise"]:
                db["clicks"]["button_wise"][new_name] = db["clicks"]["button_wise"].pop(old_name)
            save_db(db)
            bot.send_message(message.chat.id, f"✅ Button text updated from <b>{old_name}</b> to <b>{new_name}</b> successfully!")

    elif state.startswith("edit_btn_link_process_"):
        btn_idx = int(state.split("_")[-1])
        admin_states.pop(user_id, None)
        if message.content_type == 'text' and (message.text.startswith("http://") or message.text.startswith("https://")):
            db["buttons"][btn_idx]["value"] = message.text.strip()
            save_db(db)
            bot.send_message(message.chat.id, f"✅ Link for button <b>{db['buttons'][btn_idx]['text']}</b> updated successfully!")
        else: bot.send_message(message.chat.id, "❌ Invalid URL! Aborted.")

    elif state == "awaiting_verification_btn_text":
        if message.content_type == 'text':
            db["verification_btn_text"] = message.text.strip()
            save_db(db)
            bot.send_message(message.chat.id, f"✅ Verification button text updated to: <code>{message.text}</code>")
        admin_states.pop(user_id, None)

    elif state == "awaiting_broadcast_btn_text":
        if message.content_type == 'text':
            db["broadcast_btn_text"] = message.text.strip()
            save_db(db)
            bot.send_message(message.chat.id, f"✅ Auto link button text updated to: <code>{message.text}</code>")
        admin_states.pop(user_id, None)
        
    elif state == "awaiting_channels":
        parsed = [x.strip() for x in re.split(r'[\s,]+', message.text) if x.strip().startswith("@")]
        db["channels"] = parsed
        save_db(db)
        bot.send_message(message.chat.id, f"✅ Force Join channels synced. Total channels: {len(parsed)}")
        admin_states.pop(user_id, None)
        
    elif state.startswith("broadcast_"):
        mode = state.split("_")[1]
        admin_states.pop(user_id, None)
        
        all_users = list(db["users"].keys())
        total_targets = len(all_users)
        
        if total_targets == 0:
            bot.send_message(message.chat.id, "❌ Infrastructure user base array empty.")
            return
            
        status = bot.send_message(message.chat.id, f"⏳ Deploying transmission... Progress: 0/{total_targets}")
        success, failed = 0, 0
        
        # LINK AUTO-EXTRACTION LOGIC
        source_text = message.text if message.content_type == 'text' else message.caption
        detected_link = extract_first_link(source_text)
        
        broadcast_markup = None
        if detected_link:
            broadcast_markup = types.InlineKeyboardMarkup()
            btn_txt = db.get("broadcast_btn_text", "👉 Register Now")
            broadcast_markup.add(types.InlineKeyboardButton(text=btn_txt, url=detected_link, callback_data="dynamic_broadcast_click"))
        
        for idx, target_uid in enumerate(all_users, start=1):
            user_str = str(target_uid)
            
            # Ensure the user dictionary has tracking fields structure safely
            if user_str in db["users"] and not isinstance(db["users"][user_str], dict):
                db["users"][user_str] = {"joined": time.time(), "clicks": 0, "banned": False, "last_pin_id": None}
            elif user_str in db["users"]:
                db["users"][user_str].setdefault("last_pin_id", None)

            # 1. AUTO-UNPIN PREVIOUS MESSAGE LOGIC
            old_pin_id = db["users"].get(user_str, {}).get("last_pin_id")
            if old_pin_id:
                try:
                    bot.unpin_chat_message(target_uid, old_pin_id)
                except Exception:
                    pass # Shield if user cleared history or chat doesn't exist
            
            # 2. DISPATCH BROADCAST MESSAGE PAYLOAD
            sent_msg = None
            try:
                if mode == "forward":
                    sent_msg = bot.forward_message(target_uid, message.chat.id, message.message_id)
                else:
                    if message.content_type == 'text':
                        sent_msg = bot.send_message(target_uid, message.text, reply_markup=broadcast_markup)
                    elif message.content_type == 'photo':
                        sent_msg = bot.send_photo(target_uid, message.photo[-1].file_id, caption=message.caption, reply_markup=broadcast_markup)
                    elif message.content_type == 'video':
                        sent_msg = bot.send_video(target_uid, message.video.file_id, caption=message.caption, reply_markup=broadcast_markup)
                    elif message.content_type == 'document':
                        sent_msg = bot.send_document(target_uid, message.document.file_id, caption=message.caption, reply_markup=broadcast_markup)
                    elif message.content_type == 'voice':
                        sent_msg = bot.send_voice(target_uid, message.voice.file_id, caption=message.caption, reply_markup=broadcast_markup)
                
                # 3. AUTO-PIN NEW RECENT MESSAGE LOGIC
                if sent_msg:
                    try:
                        bot.pin_chat_message(target_uid, sent_msg.message_id, disable_notification=False)
                        db["users"][user_str]["last_pin_id"] = sent_msg.message_id
                    except Exception:
                        pass
                success += 1
            except Exception:
                failed += 1
                
            if idx % 20 == 0 or idx == total_targets:
                try:
                    bot.edit_message_text(
                        f"📢 <b>Mass Broadcast Transmission Logs:</b>\n\n"
                        f"👥 Total Target Baseline: <code>{total_targets}</code>\n"
                        f"✅ Sent Successfully: <code>{success}</code>\n"
                        f"❌ Failed Deliveries: <code>{failed}</code>\n"
                        f"🔗 Link Extracted: <code>{detected_link if detected_link else 'No Link Found'}</code>\n"
                        f"📌 Auto-Pin Status: <code>Active (Recent Post Pinned)</code>",
                        message.chat.id, status.message_id
                    )
                except Exception: pass
            time.sleep(0.04)
            
        save_db(db) # Commit newly updated pin matrices seamlessly to state
        bot.send_message(message.chat.id, "🏁 <b>Broadcast Delivery Pipeline Task Finished. All recent posts have been auto-pinned!</b>")

if __name__ == "__main__":
    keep_alive()
    logger.info("Bot logic mapping loaded smoothly.")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=90)
        except Exception as err:
            logger.error(f"Polling crash shielded event: {err}")
            time.sleep(5)
