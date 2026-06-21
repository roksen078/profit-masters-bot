import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import random
import json  # Permanent database file ke liye

# --- CONFIGURATION & INITIALIZATION ---
TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DB_FILE = "users_db.json"

# --- JSON DATABASE UTILITIES (PERMANENT STORAGE) ---
def load_users():
    """File se registered users ka data safe load karne ke liye"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                return set(data.get("users", []))
        except Exception:
            return set()
    return set()

def save_user_to_db(user_id):
    """Naye users ko permanent file me safe append karne ke liye"""
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        try:
            with open(DB_FILE, "w") as f:
                json.dump({"users": list(users)}, f)
        except Exception as e:
            print(f"Error saving database: {e}")

# --- SYSTEM DATA MATRIX (100% SAME AS YOUR ORIGINAL) ---
db = {
    "maintenance": False,
    "welcome_photo": "https://placehold.co/600x400/png", 
    "welcome_caption": "🎉 <b>Welcome to Profit Masters!</b>\n\n🎁 Your signup bonus is ready.\n👇 Join channels and click verify.",
    "free_code_btn_text": "🎁 Get My Free Code",
    "broadcast_btn_text": "🔥 Join Channel",
    
    # CONTROL SETTINGS
    "verification_delay_enabled": True, 
    "verification_text": "⏳ Processing your request... Please wait 5 seconds.", 
    
    "custom_buttons": [
        {"text": "🚀 Claim ₹500", "url": "https://t.me/telegram"},
        {"text": "🎁 Unlock Code", "url": "https://t.me/telegram"},
        {"text": "🎯 Claim bonus", "url": "https://t.me/telegram"},
        {"text": "💎 VIP GIFT", "url": "https://t.me/telegram"}
    ],
    "channels": ["@ch1", "@ch2"], 
    "url_clicks": 0
}

ADMIN_ID = 123456789  # ⚠️ APNA REAL TELEGRAM NUMERIC ADMIN ID YAHA DAALEIN

# Admin Pipeline State Machines
STATE_NONE = "NONE"
STATE_EDIT_PHOTO = "EDIT_PHOTO"
STATE_EDIT_CAPTION = "EDIT_CAPTION"
STATE_ADD_BTN_NAME = "ADD_BTN_NAME"
STATE_ADD_BTN_URL = "ADD_BTN_URL"
STATE_EDIT_FREE_BTN = "EDIT_FREE_BTN"
STATE_EDIT_VERIFY_TEXT = "EDIT_VERIFY_TEXT"
STATE_UPDATE_CHANNELS = "UPDATE_CHANNELS"
STATE_BROADCAST_TEXT = "STATE_BROADCAST_TEXT"
STATE_FORWARD_BROADCAST = "STATE_FORWARD_BROADCAST"
STATE_COPY_BROADCAST = "STATE_COPY_BROADCAST"

admin_states = {}
temp_btn_data = {}

def is_admin(user_id):
    return int(user_id) == int(ADMIN_ID)

# --- FORCE JOIN CHECKS PROTOCOL ---
def check_user_joined_all(user_id):
    if not db["channels"]:
        return True
    for channel in db["channels"]:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False 
    return True

# --- REBUILD DYNAMIC REPLIES PANEL ---
def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # 100% SAME AS YOUR ORIGINAL SCREENSHOT MENU
    markup.add(
        KeyboardButton("📊 Analytics & Stats"),
        KeyboardButton("⚙️ Default Configuration Settings"),
        KeyboardButton("⏩ Forward Broadcast"),
        KeyboardButton("📝 Copy Broadcast"),
        KeyboardButton("📸 Change Photo"),
        KeyboardButton("✍️ Change Caption"),
        KeyboardButton("+ Add Welcome Button"),
        KeyboardButton("📝 Edit Button Text"),
        KeyboardButton("🔗 Edit Button URL"),
        KeyboardButton("- Remove Welcome Button"),
        KeyboardButton("📝 Edit Free Code Btn Text"),
        KeyboardButton("📝 Broadcast Button Text"),
        KeyboardButton("🔗 Update Channels"),
        KeyboardButton("🎚️ Maintenance Mode"),
        KeyboardButton("🔄 Reset URL Click Counter")
    )
    
    # 🌟 AAPKE CONTROLS EKDOM NEECHE ALAG SE ADJUST HAIN
    delay_status = "🟢 Delay Status: ON" if db.get("verification_delay_enabled", True) else "🔴 Delay Status: OFF"
    markup.add(
        KeyboardButton(delay_status),
        KeyboardButton("⏳ Edit Verification Text"),
        KeyboardButton("📥 Export Users Data")
    )
    return markup

# --- USER LANDING PROXY ROUTER ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    save_user_to_db(user_id) # background me ID auto permanent save ho jayegi
    
    if db.get("maintenance", False) and not is_admin(user_id):
        return
        
    # Layout perfectly maintained: Pehle 4 custom buttons rows me, fir niche free code wala
    markup = InlineKeyboardMarkup(row_width=2)
    
    btns_list = [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in db["custom_buttons"]]
    for i in range(0, len(btns_list), 2):
        markup.row(*btns_list[i:i+2])
        
    markup.add(InlineKeyboardButton(text=db["free_code_btn_text"], callback_data="get_free_code"))
    
    try:
        bot.send_photo(
            chat_id=message.chat.id,
            photo=db["welcome_photo"],
            caption=db["welcome_caption"],
            parse_mode="HTML",
            reply_markup=markup
        )
    except Exception:
        bot.send_message(
            chat_id=message.chat.id,
            text=db["welcome_caption"],
            parse_mode="HTML",
            reply_markup=markup
        )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        return
    admin_states[message.from_user.id] = STATE_NONE
    bot.send_message(message.chat.id, "🛠 *Profit Masters Administrative Control Console:*", parse_mode="Markdown", reply_markup=get_admin_keyboard())

# --- USER TELEGRAM ACTION EXECUTOR (NON-BLOCKING PARALLEL TIMERS) ---
@bot.callback_query_handler(func=lambda call: call.data == "get_free_code")
def handle_reward_claim(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_user_joined_all(user_id):
        error_msg = (
            "<b>⚠️ Aapne Join Nahi Kiya!</b>\n\n"
            "Kripaya upar diye gaye channels join karein.\n\n"
            "📌 <b>Zaruri:</b> Channels ko Pin karke rakho, tabhi code milega!"
        )
        bot.send_message(chat_id, error_msg, parse_mode="HTML")
        return

    db["url_clicks"] += 1
    
    if db.get("verification_delay_enabled", True):
        status_msg = bot.send_message(chat_id, db.get("verification_text", "⏳ Processing..."))
        
        # Is thread logic se doosre users 1 second ke liye bhi freeze nahi hote
        def send_code_delayed():
            generated_code = f"IW7-PROMO-{random.randint(100000, 999999)}"
            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except Exception:
                pass
            bot.send_message(chat_id, f"🎁 <b>Verification Successful!</b>\n\n🔑 Your Code: <code>{generated_code}</code>", parse_mode="HTML")
            
        threading.Timer(5.0, send_code_delayed).start()
    else:
        generated_code = f"IW7-PROMO-{random.randint(100000, 999999)}"
        bot.send_message(chat_id, f"🎁 <b>Verification Successful!</b>\n\n🔑 Your Code: <code>{generated_code}</code>", parse_mode="HTML")

# --- ADMINISTRATIVE PIPELINE ENGINE HANDLERS ---
@bot.message_handler(func=lambda message: is_admin(message.from_user.id), content_types=['text', 'photo', 'video', 'document', 'animation'])
def handle_admin_inputs(message):
    user_id = message.from_user.id
    text = message.text if message.content_type == 'text' else ""
    state = admin_states.get(user_id, STATE_NONE)
    
    if text == "🎚️ Maintenance Mode":
        db["maintenance"] = not db["maintenance"]
        status = "ENABLED 🛑" if db["maintenance"] else "DISABLED 🟢"
        bot.send_message(message.chat.id, f"✅ Maintenance Mode is now {status}", reply_markup=get_admin_keyboard())
        return

    elif text.startswith("🟢 Delay Status:") or text.startswith("🔴 Delay Status:"):
        db["verification_delay_enabled"] = not db["verification_delay_enabled"]
        status = "ENABLED 🟢" if db["verification_delay_enabled"] else "DISABLED 🔴"
        bot.send_message(message.chat.id, f"✅ Verification Delay is now {status}.", reply_markup=get_admin_keyboard())
        return

    elif text == "⏳ Edit Verification Text":
        admin_states[user_id] = STATE_EDIT_VERIFY_TEXT
        bot.send_message(message.chat.id, f"📥 Send me the new text loader string:\n\n<b>Current:</b> <code>{db.get('verification_text')}</code>", parse_mode="HTML")
        return

    # ✨ 1-CLICK DATA EXPORT CODE
    elif text == "📥 Export Users Data":
        users = load_users()
        total_users = len(users)
        if total_users == 0:
            bot.send_message(message.chat.id, "❌ Database me abhi koi user nahi hai.")
            return
            
        file_name = "profit_masters_users.txt"
        with open(file_name, "w") as f:
            for uid in users:
                f.write(f"{uid}\n")
                
        with open(file_name, "rb") as f:
            bot.send_document(
                chat_id=message.chat.id,
                document=f,
                caption=f"📊 <b>Profit Masters User Database Backup</b>\n\n👥 Total Unique Users: <code>{total_users}</code>\n\n💡 <i>Is file ko safe rakhein, isme aapke saare active users ki Telegram IDs hain!</i>",
                parse_mode="HTML"
            )
        os.remove(file_name) # Server clean setup
        return

    elif text == "⏩ Forward Broadcast":
        admin_states[user_id] = STATE_FORWARD_BROADCAST
        bot.send_message(message.chat.id, "📥 Muze wo message bhejein jise aap sabhi users ko <b>FORWARD</b> karna chahte hain:", parse_mode="HTML")
        return

    elif text == "📝 Copy Broadcast":
        admin_states[user_id] = STATE_COPY_BROADCAST
        bot.send_message(message.chat.id, "📥 Muze wo post bhejein jise aap bina credit/tag ke direct <b>COPY BROADCAST</b> karna chahte hain:", parse_mode="HTML")
        return

    elif text == "📸 Change Photo":
        admin_states[user_id] = STATE_EDIT_PHOTO
        bot.send_message(message.chat.id, "📥 Send me the new photo URL:")
        return

    elif text == "✍️ Change Caption":
        admin_states[user_id] = STATE_EDIT_CAPTION
        bot.send_message(message.chat.id, "📥 Send me the new HTML caption:")
        return

    elif text == "📊 Analytics & Stats":
        users = load_users()
        bot.send_message(message.chat.id, f"📊 <b>Core Analytics Database Node:</b>\n\n👥 Total Unique Users: <code>{len(users)}</code>\n⚡ Total Verification Clicks: <code>{db['url_clicks']}</code>", parse_mode="HTML")
        return

    elif text == "🔄 Reset URL Click Counter":
        db["url_clicks"] = 0
        bot.send_message(message.chat.id, "✅ URL Click counter has been reset to 0.")
        return

    elif text == "+ Add Welcome Button":
        admin_states[user_id] = STATE_ADD_BTN_NAME
        bot.send_message(message.chat.id, "📥 Enter the Text/Name for the new button:")
        return

    elif text == "- Remove Welcome Button":
        if not db["custom_buttons"]:
            bot.send_message(message.chat.id, "❌ No buttons available to remove.")
            return
        markup = InlineKeyboardMarkup()
        for idx, btn in enumerate(db["custom_buttons"]):
            markup.add(InlineKeyboardButton(text=f"❌ {btn['text']}", callback_data=f"del_{idx}"))
        bot.send_message(message.chat.id, "Select a button to delete permanently:", reply_markup=markup)
        return

    elif text == "📝 Edit Free Code Btn Text":
        admin_states[user_id] = STATE_EDIT_FREE_BTN
        bot.send_message(message.chat.id, f"📥 Send me the new name for the main button:\n\n<b>Current:</b> {db['free_code_btn_text']}")
        return

    elif text == "📝 Broadcast Button Text":
        admin_states[user_id] = STATE_BROADCAST_TEXT
        bot.send_message(message.chat.id, f"📥 Send me the text for the broadcast link button:\n\n<b>Current:</b> {db['broadcast_btn_text']}")
        return

    elif text == "🔗 Update Channels":
        admin_states[user_id] = STATE_UPDATE_CHANNELS
        bot.send_message(message.chat.id, "📥 Send channels separated by space (e.g. @ch1 @ch2 @ch3):")
        return

    # --- STATE PIPELINE RECONSTRUCTION & LOGIC RESOLUTION TREE ---
    if state == STATE_FORWARD_BROADCAST:
        admin_states[user_id] = STATE_NONE
        users = load_users()
        success = 0
        bot.send_message(message.chat.id, f"🚀 Forward Broadcast started for {len(users)} users...")
        for uid in users:
            try:
                bot.forward_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
                success += 1
            except Exception:
                pass
        bot.send_message(message.chat.id, f"📢 <b>Forward Broadcast Finished!</b>\n\n✅ Successfully delivered to: <code>{success}</code> users.", parse_mode="HTML")
        return

    elif state == STATE_COPY_BROADCAST:
        admin_states[user_id] = STATE_NONE
        users = load_users()
        success = 0
        bot.send_message(message.chat.id, f"🚀 Copy Broadcast started for {len(users)} users...")
        for uid in users:
            try:
                bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
                success += 1
            except Exception:
                pass
        bot.send_message(message.chat.id, f"📢 <b>Copy Broadcast Finished!</b>\n\n✅ Successfully delivered to: <code>{success}</code> users.", parse_mode="HTML")
        return

    elif state == STATE_EDIT_VERIFY_TEXT:
        db["verification_text"] = text
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, "✅ Verification text customized successfully!", reply_markup=get_admin_keyboard())
        
    elif state == STATE_EDIT_PHOTO:
        db["welcome_photo"] = text
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, "✅ Welcome Photo updated!", reply_markup=get_admin_keyboard())
        
    elif state == STATE_EDIT_CAPTION:
        db["welcome_caption"] = text
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, "✅ Welcome Caption updated!", reply_markup=get_admin_keyboard())

    elif state == STATE_ADD_BTN_NAME:
        temp_btn_data[user_id] = {"text": text}
        admin_states[user_id] = STATE_ADD_BTN_URL
        bot.send_message(message.chat.id, f"📥 Now send the full URL/Link for button <b>{text}</b>:", parse_mode="HTML")

    elif state == STATE_ADD_BTN_URL:
        if text.startswith("http://") or text.startswith("https://") or text.startswith("t.me/"):
            name = temp_btn_data[user_id]["text"]
            db["custom_buttons"].append({"text": name, "url": text})
            admin_states[user_id] = STATE_NONE
            bot.send_message(message.chat.id, f"✅ Button <b>{name}</b> added successfully!", parse_mode="HTML", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(message.chat.id, "⚠️ Invalid link format. Send a valid URL string:")

    elif state == STATE_EDIT_FREE_BTN:
        db["free_code_btn_text"] = text
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, f"✅ Main action button text changed to: <b>{text}</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())

    elif state == STATE_BROADCAST_TEXT:
        db["broadcast_btn_text"] = text
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, f"✅ Broadcast link button text changed to: <b>{text}</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())

    elif state == STATE_UPDATE_CHANNELS:
        ch_list = text.split()
        db["channels"] = ch_list
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, f"✅ Target authentication channels updated to:\n<code>{', '.join(ch_list)}</code>", parse_mode="HTML", reply_markup=get_admin_keyboard())

# --- BUTTON DELETION EXECUTION HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("del_"))
def handle_button_deletion(call):
    if not is_admin(call.from_user.id):
        return
    idx = int(call.data.split("_")[1])
    try:
        removed = db["custom_buttons"].pop(idx)
        bot.answer_callback_query(call.id, f"Deleted: {removed['text']}")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✅ Button removed permanently from database matrix structure.")
    except Exception:
        bot.answer_callback_query(call.id, "Error in processing deletion.")

# --- FLASK ALIVE SYSTEM ---
@app.route('/')
def home():
    return "🚀 System Operational: Profit Masters V3 Core Online!", 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.polling(none_stop=True)
