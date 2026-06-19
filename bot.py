import telebot
from telebot import types
import json
import os
import re
import time
import threading
import logging
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Profit Masters Bot V2 Running..."
    
    def run():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

def keep_alive():
    server = Thread(target=run)
    server.daemon = True
    server.start()
    
    logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s : %(message)s"
)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

DATA_DIR = "data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
def load_json(file_name, default):
    try:
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(e)

    return default


def save_json(file_name, data):
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(e)
        users = load_json(USERS_FILE, {})

settings = load_json(
    SETTINGS_FILE,
    {
        "welcome_photo": "",
        "welcome_caption": "",
        "channels": [],
        "buttons": [],
        "force_join": True,
        "maintenance": False
    }
)


def save_settings():
    save_json(SETTINGS_FILE, settings)
    def save_users():
    save_json(USERS_FILE, users)


def get_setting(key, default=None):
    return settings.get(key, default)


def set_setting(key, value):
    settings[key] = value
    save_settings()


def is_maintenance():
    return settings.get("maintenance", False)
    def is_admin(message):
    return message.from_user.id == ADMIN_ID


    def add_user(user_id):
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "joined": True,
            "blocked": False,
            "date": int(time.time())
        }
        save_users()


    def total_users():
    return len(users)


def get_user(user_id):
    return users.get(str(user_id), {})


def set_user_value(user_id, key, value):
    user_id = str(user_id)

    if user_id not in users:
        add_user(user_id)

    users[user_id][key] = value
    save_users()


def get_user_value(user_id, key, default=None):
    return users.get(str(user_id), {}).get(key, default)
    def create_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = settings.get("buttons", [])

    for i in range(0, min(len(buttons), 4), 2):
        row = []

        for btn in buttons[i:i + 2]:
            row.append(
                types.InlineKeyboardButton(
                    text=btn["text"],
                    url=btn["url"]
                )
            )

        markup.row(*row)
        markup.row(
        types.InlineKeyboardButton(
            "🎁 Get My Free Code",
            callback_data="get_code"
        )
    )

    return markup
    def check_force_join(user_id):
    channels = settings.get("channels", [])

    for channel in channels:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False

    return True
    def send_force_join(message):
    markup = types.InlineKeyboardMarkup(row_width=1)

    for channel in settings.get("channels", []):
        try:
            chat = bot.get_chat(channel)
            invite = bot.export_chat_invite_link(channel)

            markup.add(
                types.InlineKeyboardButton(
                    f"📢 Join {chat.title}",
                    url=invite
                )
            )
        except Exception:
            pass

    markup.add(
        types.InlineKeyboardButton(
            "✅ I've Joined",
            callback_data="check_join"
        )
    )

    bot.send_message(
        message.chat.id,
        "⚠️ Please join all required channels first.",
        reply_markup=markup
    )
    @bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if check_force_join(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "✅ Verification successful!"
        )

        try:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass

        send_welcome(call.message)

    else:
        bot.answer_callback_query(
            call.id,
            "❌ You haven't joined all channels yet.",
            show_alert=True
        )def send_welcome(message):
    add_user(message.from_user.id)

    photo = get_setting("welcome_photo", "")
    caption = get_setting("welcome_caption", "")

    if not caption:
        caption = (
            "👋 <b>Welcome!</b>\n\n"
            "Click the button below to claim your free code."
        )

    markup = create_main_keyboard()

    try:
        if photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption=caption,
                parse_mode="HTML",
                reply_markup=markup
            )
            else:
            bot.send_message(
                message.chat.id,
                caption,
                parse_mode="HTML",
                reply_markup=markup
            )

    except Exception:
        bot.send_message(
            message.chat.id,
            caption,
            parse_mode="HTML",
            reply_markup=markup
        )
@bot.message_handler(commands=["start"])
def start_command(message):
    if is_maintenance() and not is_admin(message):
        bot.reply_to(
            message,
            "🚧 Bot is currently under maintenance."
        )
        return

    if settings.get("force_join", True):
        if not check_force_join(message.from_user.id):
            send_force_join(message)
            return

    send_welcome(message)
    @bot.message_handler(commands=["admin"])
def admin_panel(message):
    if not is_admin(message):
        return

    text = (
        "⚙️ <b>Admin Panel</b>\n\n"
        "Choose an option below."
    )

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton(
            "🖼 Welcome Photo",
            callback_data="admin_photo"
        ),
        types.InlineKeyboardButton(
            "📝 Welcome Caption",
            callback_data="admin_caption"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "🔘 Buttons",
            callback_data="admin_buttons"
        ),
        types.InlineKeyboardButton(
            "🎁 Get My Free Code",
            callback_data="admin_code"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "📢 Force Join",
            callback_data="admin_channels"
        ),
        types.InlineKeyboardButton(
            "🛠 Maintenance",
            callback_data="admin_maintenance"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "📊 Statistics",
            callback_data="admin_stats"
        ),
        types.InlineKeyboardButton(
            "📤 Broadcast",
            callback_data="admin_broadcast"
        )
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )
    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
    if not is_admin(call.message):
        return

    bot.answer_callback_query(call.id)

    if call.data == "admin_photo":
        bot.send_message(
            call.message.chat.id,
            "🖼 Send the new welcome photo."
        )
        bot.register_next_step_handler(
            call.message,
            save_welcome_photo
        )
        elif call.data == "admin_caption":
        bot.send_message(
            call.message.chat.id,
            "📝 Send the new welcome caption."
        )
        bot.register_next_step_handler(
            call.message,
            save_welcome_caption
        )

    elif call.data == "admin_buttons":
        bot.send_message(
            call.message.chat.id,
            "🔘 Send buttons in this format:\n\nButton Name | https://example.com"
        )
        bot.register_next_step_handler(
            call.message,
            save_buttons
        )
elif call.data == "admin_code":
        bot.send_message(
            call.message.chat.id,
            "🎁 Send your Get My Free Code text."
        )
        bot.register_next_step_handler(
            call.message,
            save_code
        )

    elif call.data == "admin_channels":
        bot.send_message(
            call.message.chat.id,
            "📢 Send channel usernames.\nOne username per line.\nExample:\n@channel1\n@channel2"
        )
        bot.register_next_step_handler(
            call.message,
            save_channels
        )
elif call.data == "admin_maintenance":
        settings["maintenance"] = not settings.get("maintenance", False)
        save_settings()

        status = "🟢 OFF" if not settings["maintenance"] else "🔴 ON"

        bot.answer_callback_query(
            call.id,
            f"Maintenance Mode: {status}"
        )

        admin_panel(call.message)

    elif call.data == "admin_stats":
        bot.send_message(
            call.message.chat.id,
            f"👥 Total Users: {total_users()}"
        )
elif call.data == "admin_broadcast":
        bot.send_message(
            call.message.chat.id,
            "📤 Send the broadcast message."
        )
        bot.register_next_step_handler(
            call.message,
            broadcast_message
        )
def save_welcome_photo(message):
    if not message.photo:
        bot.reply_to(message, "❌ Please send a photo.")
        return

    file_id = message.photo[-1].file_id
    set_setting("welcome_photo", file_id)

    bot.reply_to(
        message,
        "✅ Welcome photo updated."
    )


def save_welcome_caption(message):
    set_setting("welcome_caption", message.text)

    bot.reply_to(
        message,
        "✅ Welcome caption updated."
    )
def save_buttons(message):
    buttons = []

    for line in message.text.splitlines():
        if "|" not in line:
            continue

        text, url = line.split("|", 1)

        buttons.append({
            "text": text.strip(),
            "url": url.strip()
        })

    settings["buttons"] = buttons
    save_settings()

    bot.reply_to(
        message,
        "✅ Buttons updated."
    )


def save_code(message):
    set_setting("code", message.text)

    bot.reply_to(
        message,
        "✅ Get My Free Code updated."
    )
def save_channels(message):
    channels = []

    for line in message.text.splitlines():
        line = line.strip()

        if line:
            channels.append(line)

    settings["channels"] = channels
    save_settings()

    bot.reply_to(
        message,
        "✅ Force Join channels updated."
    )


def broadcast_message(message):
    sent = 0

    for user_id in users.keys():
        try:
            bot.copy_message(
                int(user_id),
                message.chat.id,
                message.message_id
            )
            sent += 1
        except Exception:
            pass
            bot.reply_to(
        message,
        f"✅ Broadcast sent to {sent} users."
    )


bot.infinity_polling(
    none_stop=True,
    skip_pending=True
)
