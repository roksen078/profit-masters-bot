import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import random
import json
import re
import uuid  # Unique tracker keys generate karne ke liye

# --- CONFIGURATION & INITIALIZATION ---
TOKEN = os.getenv("BOT_TOKEN", "8801329011:AAEN_Lxz5cTa3tsVDBW0vfYEY30eO-Ogkzk")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DB_FILE = "users_db.json"
db_lock = threading.Lock()

# --- SYSTEM SETTINGS DEFAULT MATRIX ---
DEFAULT_SETTINGS = {
    "users": [],
    "maintenance": False,
    "welcome_photo": "https://placehold.co/600x400/png", 
    "welcome_caption": "🎉 <b>Welcome to Profit Masters!</b>\n\n🎁 Your signup bonus is ready.\n👇 Join channels and click verify.",
    "free_code_btn_text": "🎁 Get My Free Code",
    "broadcast_btn_text": "👉 Register Now", 
    "verification_delay_enabled": True, 
    "verification_text": "⏳ Processing your request... Please wait 5 seconds.", 
    "error_text": "<b>⚠️ Aapne Join Nahi Kiya!</b>\n\nKripaya upar diye gaye channels join karein.\n\n📌 <b>Zaruri:</b> Channels ko Pin karke rakho, tabhi code milega!",
    "custom_buttons": [
        {"text": "🚀 Claim ₹500", "url": "https://t.me/telegram"},
        {"text": "🎁 Unlock Code", "url": "https://t.me/telegram"},
        {"text": "🎯 Claim bonus", "url": "https://t.me/telegram"},
        {"text": "💎 VIP GIFT", "url": "https://t.me/telegram"}
    ],
    "channels": ["@ch1", "@ch2"], 
    "broadcast_links": {}  # Unique tracking link storage node
}

def load_system_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                for key in DEFAULT_SETTINGS:
                    if key not in data:
                        data[key] = DEFAULT_SETTINGS[key]
                return data
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_system_data(data):
    with db_lock:
        try:
            data_copy = data.copy()
            if "users" in data_copy:
                if isinstance(data_copy["users"], set):
                    data_copy["users"] = list(data_copy["users"])
                elif not isinstance(data_copy["users"], list):
                    data_copy["users"] = []
            with open(DB_FILE, "w") as f:
                json.dump(data_copy, f, indent=4)
        except Exception as e:
            print(f"Database structural save error: {e}")

sys_db = load_system_data()

if "users" not in sys_db or not isinstance(sys_db["users"], (list, set)):
    sys_db["users"] = set()
else:
    sys_db["users"] = set(sys_db["users"])

if "broadcast_links" not in sys_db:
    sys_db["broadcast_links"] = {}

def save_user_to_db(user_id):
    try:
        if not isinstance(sys_db["users"], set):
            sys_db["users"] = set(sys_db["users"])
        if user_id not in sys_db["users"]:
            sys_db["users"].add(user_id)
            save_system_data(sys_db)
    except Exception as e:
        print(f"User registration bypassed: {e}")

ADMIN_ID = 1908832842  

STATE_NONE = "NONE"
STATE_EDIT_PHOTO = "EDIT_PHOTO"
STATE_EDIT_CAPTION = "EDIT_CAPTION"
STATE_ADD_BTN_NAME = "ADD_BTN_NAME"
STATE_ADD_BTN_URL = "ADD_BTN_URL"
STATE_EDIT_FREE_BTN = "EDIT_FREE_BTN"
STATE_EDIT_VERIFY_TEXT = "EDIT_VERIFY_TEXT"
STATE_EDIT_ERROR_TEXT = "EDIT_ERROR_TEXT"
STATE_UPDATE_CHANNELS = "UPDATE_CHANNELS"
STATE_BROADCAST_TEXT = "STATE_BROADCAST_TEXT"
STATE_FORWARD_BROADCAST = "FORWARD_BROADCAST"
STATE_COPY_BROADCAST = "COPY_BROADCAST"
STATE_EDIT_BTN_TEXT = "EDIT_BTN_TEXT"
STATE_EDIT_BTN_URL = "EDIT_BTN_URL"

admin_states = {}
temp_btn_data = {}

def is_admin(user_id):
    return int(user_id) == int(ADMIN_ID)

def check_user_joined_all(user_id):
    if not sys_db["channels"]:
        return True
    for channel in sys_db["channels"]:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False 
    return True

def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
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
        KeyboardButton("🔄 Reset All Link Tracking Data")
    )
    delay_status = "🟢 Delay Status: ON" if sys_db.get("verification_delay_enabled", True) else "🔴 Delay Status: OFF"
    markup.add(
        KeyboardButton(delay_status),
        KeyboardButton("⏳ Edit Verification Text"),
        KeyboardButton("📝 Edit Join Error Text"),
        KeyboardButton("📥 Export Users Data")
    )
    return markup

def extract_first_link(text):
    if not text:
        return None
    urls = re.findall(r'(https?://\S+|t\.me/\S+)', text)
    return urls[0] if urls else None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    save_user_to_db(user_id)
    
    if sys_db.get("maintenance", False) and not is_admin(user_id):
        bot.send_message(message.chat.id, "🚧 <b>Bot is currently under maintenance. Please try again later.</b>", parse_mode="HTML")
        return
        
    markup = InlineKeyboardMarkup(row_width=2)
    btns_list = [InlineKeyboardButton(text=btn["text"], url=btn["url"]) for btn in sys_db["custom_buttons"]]
    for i in range(0, len(btns_list), 2):
        markup.row(*btns_list[i:i+2])
        
    markup.add(InlineKeyboardButton(text=sys_db["free_code_btn_text"], callback_data="get_free_code"))
    
    try:
        bot.send_photo(
            chat_id=message.chat.id,
            photo=sys_db["welcome_photo"],
            caption=sys_db["welcome_caption"],
            parse_mode="HTML",
            reply_markup=markup
        )
    except Exception:
        bot.send_message(
            chat_id=message.chat.id,
            text=sys_db["welcome_caption"],
            parse_mode="HTML",
            reply_markup=markup
        )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        return
    admin_states[message.from_user.id] = STATE_NONE
    bot.send_message(message.chat.id, "🛠 *Profit Masters Administrative Control Console:*", parse_mode="Markdown", reply_markup=get_admin_keyboard())

# --- USER SYSTEM RUNTIME CALLBACK INTERCEPTOR ---
@bot.callback_query_handler(func=lambda call: call.data == "get_free_code")
def handle_reward_claim(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if sys_db.get("verification_delay_enabled", True):
        status_msg = bot.send_message(chat_id, sys_db.get("verification_text", "⏳ Processing..."))
        
        def process_verification_with_delay():
            if not check_user_joined_all(user_id):
                try:
                    bot.delete_message(chat_id, status_msg.message_id)
                except Exception:
                    pass
                error_msg = sys_db.get("error_text", "<b>⚠️ Aapne Join Nahi Kiya!</b>")
                bot.send_message(chat_id, error_msg, parse_mode="HTML")
                return

            generated_code = f"IW7-PROMO-{random.randint(100000, 999999)}"
            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except Exception:
                pass
            bot.send_message(chat_id, f"🎁 <b>Verification Successful!</b>\n\n🔑 Your Code: <code>{generated_code}</code>", parse_mode="HTML")
            
        threading.Timer(5.0, process_verification_with_delay).start()
        
    else:
        if not check_user_joined_all(user_id):
            error_msg = sys_db.get("error_text", "<b>⚠️ Aapne Join Nahi Kiya!</b>")
            bot.send_message(chat_id, error_msg, parse_mode="HTML")
            return

        generated_code = f"IW7-PROMO-{random.randint(100000, 999999)}"
        bot.send_message(chat_id, f"🎁 <b>Verification Successful!</b>\n\n🔑 Your Code: <code>{generated_code}</code>", parse_mode="HTML")

# --- BROADCAST LIVE TRACKER INTERCEPTOR ROUTER ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("track_lnk_"))
def handle_tracked_link_clicks(call):
    link_id = call.data.replace("track_lnk_", "")
    if link_id in sys_db.get("broadcast_links", {}):
        sys_db["broadcast_links"][link_id]["clicks"] += 1
        save_system_data(sys_db)
        # User ko redirect URL alert window ke through safely provide kiya jayega bina user functionality tode
        target_url = sys_db["broadcast_links"][link_id]["url"]
        bot.answer_callback_query(call.id, url=target_url)
    else:
        bot.answer_callback_query(call.id, "⚠️ Link configuration error or expired link data.", show_alert=True)

# --- ADMINISTRATIVE PIPELINE ENGINE ---
@bot.message_handler(func=lambda message: is_admin(message.from_user.id), content_types=['text', 'photo', 'video', 'document', 'animation'])
def handle_admin_inputs(message):
    user_id = message.from_user.id
    text = message.text if message.content_type == 'text' else ""
    state = admin_states.get(user_id, STATE_NONE)
    
    if text == "🎚️ Maintenance Mode":
        sys_db["maintenance"] = not sys_db["maintenance"]
        save_system_data(sys_db)
        status = "ENABLED 🛑" if sys_db["maintenance"] else "DISABLED 🟢"
        bot.send_message(message.chat.id, f"✅ Maintenance Mode is now {status}", reply_markup=get_admin_keyboard())
        return

    elif text.startswith("🟢 Delay Status:") or text.startswith("🔴 Delay Status:"):
        sys_db["verification_delay_enabled"] = not sys_db["verification_delay_enabled"]
        save_system_data(sys_db)
        status = "ENABLED 🟢" if sys_db["verification_delay_enabled"] else "DISABLED 🔴"
        bot.send_message(message.chat.id, f"✅ Verification Delay is now {status}.", reply_markup=get_admin_keyboard())
        return

    elif text == "⚙️ Default Configuration Settings":
        channels_str = ", ".join(sys_db["channels"]) if sys_db["channels"] else "None"
        delay_status_str = "ON 🟢" if sys_db["verification_delay_enabled"] else "OFF 🔴"
        m_status_str = "ON 🛑" if sys_db["maintenance"] else "OFF 🟢"
        
        config_text = (
            "⚙️ <b>Current System Configuration Master Matrix:</b>\n\n"
            f"🛠 <b>Maintenance Mode:</b> <code>{m_status_str}</code>\n"
            f"⏳ <b>Delay Status:</b> <code>{delay_status_str}</code>\n"
            f"📝 <b>Loader String:</b> <code>{sys_db['verification_text']}</code>\n"
            f"🎁 <b>Free Code Text:</b> <code>{sys_db['free_code_btn_text']}</code>\n"
            f"📢 <b>Authentication Channels:</b> <code>{channels_str}</code>\n"
            f"🖼 <b>Welcome Photo URL:</b> <code>{sys_db['welcome_photo']}</code>\n"
            f"👥 <b>Total Custom Buttons:</b> <code>{len(sys_db['custom_buttons'])}</code>"
        )
        bot.send_message(message.chat.id, config_text, parse_mode="HTML")
        return

    elif text == "⏳ Edit Verification Text":
        admin_states[user_id] = STATE_EDIT_VERIFY_TEXT
        bot.send_message(message.chat.id, f"📥 Send me the new text loader string:\n\n<b>Current:</b> <code>{sys_db.get('verification_text')}</code>", parse_mode="HTML")
        return

    elif text == "📝 Edit Join Error Text":
        admin_states[user_id] = STATE_EDIT_ERROR_TEXT
        bot.send_message(message.chat.id, f"📥 Send me the new HTML Join Error text:\n\n<b>Current:</b>\n{sys_db.get('error_text', 'None')}", parse_mode="HTML")
        return

    elif text == "📥 Export Users Data":
        total_users = len(sys_db["users"])
        if total_users == 0:
            bot.send_message(message.chat.id, "❌ Database me abhi koi user nahi hai.")
            return
            
        file_name = "profit_masters_users.txt"
        with open(file_name, "w") as f:
            for uid in sys_db["users"]:
                f.write(f"{uid}\n")
                
        with open(file_name, "rb") as f:
            bot.send_document(
                chat_id=message.chat.id,
                document=f,
                caption=f"📊 <b>Profit Masters User Database Backup</b>\n\n👥 Total Unique Users: <code>{total_users}</code>\n\n💡 <i>Is file ko safe rakhein, isme aapke saare active users ki Telegram IDs hain!</i>",
                parse_mode="HTML"
            )
        os.remove(file_name)
        return

    elif text == "⏩ Forward Broadcast":
        admin_states[user_id] = STATE_FORWARD_BROADCAST
        bot.send_message(message.chat.id, "📢 Send or forward any message/post now. Bot will auto-track link and attach tracked live button! [Mode: BROADCAST_FORWARD]:")
        return

    elif text == "📝 Copy Broadcast":
        admin_states[user_id] = STATE_COPY_BROADCAST
        bot.send_message(message.chat.id, "📢 Send or forward any message/post now. Bot will auto-track link and attach tracked live button! [Mode: BROADCAST_COPY]:")
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
        report_str = "📊 <b>Core Analytics & Broadcast Links Tracker Node:</b>\n\n"
        report_str += f"👥 Total Unique Users: <code>{len(sys_db['users'])}</code>\n"
        report_str += "───────────────────\n"
        report_str += "🔗 <b>Live Broadcast Link Clicks:</b>\n"
        
        tracked_links = sys_db.get("broadcast_links", {})
        if not tracked_links:
            report_str += "<i>Abhi koi links data tracked nahi h.</i>"
        else:
            # Sirf top 15 links text layout optimize rakhne k liye list honge
            for l_id, info in list(tracked_links.items())[-15:]:
                report_str += f"📍 <code>{info['url'][:30]}...</code> ➜ <b>{info['clicks']} Clicks</b>\n"
                
        bot.send_message(message.chat.id, report_str, parse_mode="HTML")
        return

    elif text == "🔄 Reset All Link Tracking Data":
        sys_db["broadcast_links"] = {}
        save_system_data(sys_db)
        bot.send_message(message.chat.id, "✅ Tracking node refresh completed. All broadcast link metrics reset to 0.")
        return

    elif text == "+ Add Welcome Button":
        admin_states[user_id] = STATE_ADD_BTN_NAME
        bot.send_message(message.chat.id, "📥 Enter the Text/Name for the new button:")
        return

    elif text == "- Remove Welcome Button":
        if not sys_db["custom_buttons"]:
            bot.send_message(message.chat.id, "❌ No buttons available to remove.")
            return
        markup = InlineKeyboardMarkup()
        for idx, btn in enumerate(sys_db["custom_buttons"]):
            markup.add(InlineKeyboardButton(text=f"❌ {btn['text']}", callback_data=f"del_{idx}"))
        bot.send_message(message.chat.id, "Select a button to delete permanently:", reply_markup=markup)
        return

    elif text == "📝 Edit Button Text":
        if not sys_db["custom_buttons"]:
            bot.send_message(message.chat.id, "❌ No buttons available to edit.")
            return
        markup = InlineKeyboardMarkup()
        for idx, btn in enumerate(sys_db["custom_buttons"]):
            markup.add(InlineKeyboardButton(text=f"✏️ {btn['text']}", callback_data=f"edtxt_{idx}"))
        bot.send_message(message.chat.id, "Select a button to change its text string:", reply_markup=markup)
        return

    elif text == "🔗 Edit Button URL":
        if not sys_db["custom_buttons"]:
            bot.send_message(message.chat.id, "❌ No buttons available to edit URL.")
            return
        markup = InlineKeyboardMarkup()
        for idx, btn in enumerate(sys_db["custom_buttons"]):
            markup.add(InlineKeyboardButton(text=f"🔗 {btn['text']}", callback_data=f"edurl_{idx}"))
        bot.send_message(message.chat.id, "Select a button to change its Target URL link:", reply_markup=markup)
        return

    elif text == "📝 Edit Free Code Btn Text":
        admin_states[user_id] = STATE_EDIT_FREE_BTN
        bot.send_message(message.chat.id, f"📥 Send me the new name for the main button:\n\n<b>Current:</b> {sys_db['free_code_btn_text']}")
        return

    elif text == "📝 Broadcast Button Text":
        admin_states[user_id] = STATE_BROADCAST_TEXT
        bot.send_message(message.chat.id, f"📥 Send me the text for the broadcast link button:\n\n<b>Current:</b> {sys_db.get('broadcast_btn_text', '👉 Register Now')}")
        return

    elif text == "🔗 Update Channels":
        admin_states[user_id] = STATE_UPDATE_CHANNELS
        bot.send_message(message.chat.id, "📥 Send channels separated by space (e.g. @ch1 @ch2 @ch3):")
        return

    # --- ADVANCED TRANSMISSION ENGINE (WITH INDIVIDUAL LINK TRACKING KEYS) ---
    if state in [STATE_FORWARD_BROADCAST, STATE_COPY_BROADCAST]:
        admin_states[user_id] = STATE_NONE
        
        with db_lock:
            target_users_snapshot = list(sys_db["users"])
            
        total_target = len(target_users_snapshot)
        success_count = 0
        failed_count = 0
        
        extracted_link = None
        if message.content_type == 'text':
            extracted_link = extract_first_link(message.text)
        elif message.caption:
            extracted_link = extract_first_link(message.caption)
            
        broadcast_markup = None
        if extracted_link:
            link_uuid = str(uuid.uuid4())[:8]  # Unique identification segment
            sys_db["broadcast_links"][link_uuid] = {
                "url": extracted_link,
                "clicks": 0
            }
            save_system_data(sys_db)
            
            broadcast_markup = InlineKeyboardMarkup()
            btn_label = sys_db.get("broadcast_btn_text", "👉 Register Now")
            broadcast_markup.add(InlineKeyboardButton(text=btn_label, callback_data=f"track_lnk_{link_uuid}"))
            
        for uid in target_users_snapshot:
            try:
                try:
                    bot.unpin_chat_message(chat_id=uid)
                except Exception:
                    pass
                
                if state == STATE_FORWARD_BROADCAST:
                    if broadcast_markup:
                        sent_msg = bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id, reply_markup=broadcast_markup)
                    else:
                        sent_msg = bot.forward_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
                else:
                    sent_msg = bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id, reply_markup=broadcast_markup)
                
                if sent_msg:
                    msg_id_to_pin = sent_msg.message_id if hasattr(sent_msg, 'message_id') else sent_msg.get('message_id')
                    try:
                        bot.pin_chat_message(chat_id=uid, message_id=msg_id_to_pin, disable_notification=False)
                    except Exception:
                        pass
                        
                success_count += 1
            except Exception:
                failed_count += 1
                
        link_display = extracted_link if extracted_link else "None Detected"
        log_metrics_payload = (
            "📣 <b>Mass Broadcast Transmission Logs:</b>\n\n"
            f"👥 Total Target Baseline: <code>{total_target}</code>\n"
            f"✅ Sent Successfully: <code>{success_count}</code>\n"
            f"❌ Failed Deliveries: <code>{failed_count}</code>\n"
            f"🔗 Tracked Link: <code>{link_display}</code>\n\n"
            f"💡 <i>Is link ke live clicks dekhne k liye 'Analytics & Stats' par click karein!</i>"
        )
        bot.send_message(message.chat.id, log_metrics_payload, parse_mode="HTML")
        return

    # --- PIPELINE EVALUATION ENGINE CONTINUED ---
    elif state == STATE_EDIT_VERIFY_TEXT:
        sys_db["verification_text"] = text
        save_system_data(sys_db)
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, "✅ Verification text customized successfully!", reply_markup=get_admin_keyboard())
        return

    elif state == STATE_EDIT_ERROR_TEXT:
        sys_db["error_text"] = text
        save_system_data(sys_db)
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, "✅ Join Error Text customized live successfully!", reply_markup=get_admin_keyboard())
        return

    elif state == STATE_EDIT_PHOTO:
        sys_db["welcome_photo"] = text
        save_system_data(sys_db)
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, "✅ Welcome Photo updated!", reply_markup=get_admin_keyboard())
        return
        
    elif state == STATE_EDIT_CAPTION:
        sys_db["welcome_caption"] = text
        save_system_data(sys_db)
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, "✅ Welcome Caption updated!", reply_markup=get_admin_keyboard())
        return

    elif state == STATE_ADD_BTN_NAME:
        temp_btn_data[user_id] = {"text": text}
        admin_states[user_id] = STATE_ADD_BTN_URL
        bot.send_message(message.chat.id, f"📥 Now send the full URL/Link for button <b>{text}</b>:", parse_mode="HTML")
        return

    elif state == STATE_ADD_BTN_URL:
        if text.startswith("http://") or text.startswith("https://") or text.startswith("t.me/"):
            name = temp_btn_data[user_id]["text"]
            sys_db["custom_buttons"].append({"text": name, "url": text})
            save_system_data(sys_db)
            admin_states[user_id] = STATE_NONE
            bot.send_message(message.chat.id, f"✅ Button <b>{name}</b> added successfully!", parse_mode="HTML", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(message.chat.id, "⚠️ Invalid link format. Send a valid URL string:")
        return

    elif state == STATE_EDIT_BTN_TEXT:
        target_idx = temp_btn_data[user_id]["idx"]
        old_name = sys_db["custom_buttons"][target_idx]["text"]
        sys_db["custom_buttons"][target_idx]["text"] = text
        save_system_data(sys_db)
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, f"✅ Button text changed from <b>{old_name}</b> to <b>{text}</b> successfully!", parse_mode="HTML", reply_markup=get_admin_keyboard())
        return

    elif state == STATE_EDIT_BTN_URL:
        if text.startswith("http://") or text.startswith("https://") or text.startswith("t.me/"):
            target_idx = temp_btn_data[user_id]["idx"]
            btn_name = sys_db["custom_buttons"][target_idx]["text"]
            sys_db["custom_buttons"][target_idx]["url"] = text
            save_system_data(sys_db)
            admin_states[user_id] = STATE_NONE
            bot.send_message(message.chat.id, f"✅ Target Link URL for button <b>{btn_name}</b> updated to destination payload!", parse_mode="HTML", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(message.chat.id, "⚠️ Invalid link format. Send a valid URL network protocol string:")
        return

    elif state == STATE_EDIT_FREE_BTN:
        sys_db["free_code_btn_text"] = text
        save_system_data(sys_db)
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, f"✅ Main action button text changed to: <b>{text}</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())
        return

    elif state == STATE_BROADCAST_TEXT:
        sys_db["broadcast_btn_text"] = text
        save_system_data(sys_db)
        admin_states[user_id] = STATE_NONE
        bot.send_message(message.chat.id, f"✅ Broadcast link button text changed to: <b>{text}</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())
        return

    elif text == "🔗 Update Channels":
        admin_states[user_id] = STATE_UPDATE_CHANNELS
        bot.send_message(message.chat.id, "📥 Send channels separated by space (e.g. @ch1 @ch2 @ch3):")
        return

# --- BUTTON MANIPULATION INLINE CALLBACK EXECUTOR ---
@bot.callback_query_handler(func=lambda call: call.data.startswith(('del_', 'edtxt_', 'edurl_')))
def handle_inline_callbacks(call):
    if not is_admin(call.from_user.id):
        return
    data = call.data
    if data.startswith("del_"):
        idx = int(data.split("_")[1])
        try:
            removed = sys_db["custom_buttons"].pop(idx)
            save_system_data(sys_db)
            bot.answer_callback_query(call.id, f"Deleted: {removed['text']}")
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="✅ Button removed permanently from database structure.")
        except Exception:
            bot.answer_callback_query(call.id, "Error in processing deletion.")
    elif data.startswith("edtxt_"):
        idx = int(data.split("_")[1])
        temp_btn_data[call.from_user.id] = {"idx": idx}
        admin_states[call.from_user.id] = STATE_EDIT_BTN_TEXT
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"📥 Enter the fresh Text String name for button <b>{sys_db['custom_buttons'][idx]['text']}</b>:", parse_mode="HTML")
    elif data.startswith("edurl_"):
        idx = int(data.split("_")[1])
        temp_btn_data[call.from_user.id] = {"idx": idx}
        admin_states[call.from_user.id] = STATE_EDIT_BTN_URL
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"📥 Send the new direct Redirect URL Link for button <b>{sys_db['custom_buttons'][idx]['text']}</b>:", parse_mode="HTML")

# --- PERMANENT LIFETIME KEEP-ALIVE & POLLING LOOP ---
@app.route('/')
def home():
    return "⚡ Profit Masters Bot is 100% Online and Alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
    
    print("🚀 Permanent Polling Engine Started Successfully!")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
