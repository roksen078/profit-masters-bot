import telebot
from telebot import types
import json
import os
import re
import time
from flask import Flask
from threading import Thread

# ===============================
# KEEP ALIVE (RENDER)
# ===============================

app = Flask(__name__)

@app.route("/")
def home():
    return "Profit Masters Bot is Running!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# ===============================
# ENVIRONMENT VARIABLES
# ===============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ===============================
# FILES
# ===============================

SETTINGS_FILE = "settings.json"
USERS_FILE = "users.json"
BACKUP_FOLDER = "backup"

# ===============================
# CURSOR YAHAN CHHOD DENA
# AGLE PART ME YAHI SE CODE START HOGA
# ===============================# ===============================
# JSON FUNCTIONS
# ===============================

if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        default = {
            "maintenance": False,
            "force_join": False,
            "start_message": None,
            "start_image": None,
            "channel": "",
            "buttons": [],
            "admins": [ADMIN_ID]
        }

        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4)

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)

    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


settings = load_settings()
users = load_users()

# ===============================
# CURSOR YAHI CHHOD DENA
# PART 3 YAHIN SE START HOGA
# ===============================# ===============================
# UTILITY FUNCTIONS
# ===============================

def is_admin(user_id):
    return user_id in settings.get("admins", [])


def add_user(user_id):
    global users

    if user_id not in users:
        users.append(user_id)
        save_users(users)


def get_total_users():
    return len(users)


def backup_settings():
    filename = os.path.join(BACKUP_FOLDER, "settings_backup.json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


def backup_users():
    filename = os.path.join(BACKUP_FOLDER, "users_backup.json")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)


# ===============================
# CURSOR YAHI CHHOD DENA
# PART 4 YAHIN SE START HOGA
# ===============================# ===============================
# FORCE JOIN CHECK
# ===============================

def check_force_join(user_id):
    channel = settings.get("channel", "")

    if channel == "":
        return True

    try:
        member = bot.get_chat_member(channel, user_id)

        if member.status in ["creator", "administrator", "member"]:
            return True

        return False

    except Exception:
        return False


def force_join_message():
    markup = types.InlineKeyboardMarkup()

    channel = settings.get("channel", "")

    if channel:
        markup.add(
            types.InlineKeyboardButton(
                "📢 Join Channel",
                url=f"https://t.me/{channel.replace('@','')}"
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            "✅ Joined",
            callback_data="check_join"
        )
    )

    return markup


@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):

    if check_force_join(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "✅ Verification Successful!"
        )

        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )

    else:
        bot.answer_callback_query(
            call.id,
            "❌ Please join the channel first.",
            show_alert=True
        )


# ===============================
# CURSOR YAHI CHHOD DENA
# PART 5 YAHIN SE START HOGA
# ===============================# ===============================
# START COMMAND
# ===============================

@bot.message_handler(commands=["start"])
def start(message):

    add_user(message.from_user.id)

    if not check_force_join(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "⚠️ Please join our channel first.",
            reply_markup=force_join_message()
        )
        return

    text = settings.get("start_message")

    if not text:
        text = (
            "👋 Welcome to Profit Masters Bot!\n\n"
            "Use the menu below."
        )

    markup = types.InlineKeyboardMarkup()

    buttons = settings.get("buttons", [])

    for btn in buttons:
        try:
            markup.add(
                types.InlineKeyboardButton(
                    btn["text"],
                    url=btn["url"]
                )
            )
        except:
            pass

    image = settings.get("start_image")

    try:
        if image:
            bot.send_photo(
                message.chat.id,
                image,
                caption=text,
                parse_mode="HTML",
                reply_markup=markup if buttons else None
            )
        else:
            bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML",
                reply_markup=markup if buttons else None
            )
    except:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=markup if buttons else None
        )


# ===============================
# ADMIN CHECK
# ===============================

def admin_only(message):
    return is_admin(message.from_user.id)


# ===============================
# CURSOR YAHI CHHOD DENA
# PART 6 YAHIN SE START HOGA
# ===============================# ===============================
# ADMIN PANEL
# ===============================

def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("📊 Statistics", "📢 Broadcast")
    markup.row("📝 Start Message", "🖼 Start Photo")
    markup.row("➕ Buttons", "📺 Force Join")

    markup.row("👮 Admins", "⚙ Settings")
    markup.row("💾 Backup", "♻ Restore")

    markup.row("🔑 Bot Token", "🆔 Admin ID")
    markup.row("📂 Export Users", "📥 Import Settings")

    markup.row("🔧 Maintenance", "❌ Close Panel")

    return markup


@bot.message_handler(commands=["admin"])
def admin_panel(message):

    if not admin_only(message):
        return

    bot.send_message(
        message.chat.id,
        "⚙ <b>Profit Masters Admin Panel</b>\n\n"
        "Select any option below.",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "❌ Close Panel")
def close_panel(message):

    if not admin_only(message):
        return

    bot.send_message(
        message.chat.id,
        "✅ Admin Panel Closed.",
        reply_markup=types.ReplyKeyboardRemove()
    )


# ===============================
# CURSOR YAHI CHHOD DENA
# PART 6B YAHIN SE START HOGA
# ===============================# ===============================
# STATISTICS
# ===============================

@bot.message_handler(func=lambda m: m.text == "📊 Statistics")
def statistics(message):

    if not admin_only(message):
        return

    total = get_total_users()

    text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"👥 Total Users : <b>{total}</b>\n"
        f"👮 Total Admins : <b>{len(settings.get('admins', []))}</b>\n"
        f"📺 Force Join : <b>{settings.get('channel') or 'Not Set'}</b>\n"
        f"🛠 Maintenance : <b>{'ON' if settings.get('maintenance') else 'OFF'}</b>"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML"
    )


# ===============================
# MAINTENANCE MODE
# ===============================

@bot.message_handler(func=lambda m: m.text == "🔧 Maintenance")
def maintenance_menu(message):

    if not admin_only(message):
        return

    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "🟢 ON",
            callback_data="maintenance_on"
        ),
        types.InlineKeyboardButton(
            "🔴 OFF",
            callback_data="maintenance_off"
        )
    )

    bot.send_message(
        message.chat.id,
        "🔧 Maintenance Mode",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("maintenance_"))
def maintenance_callback(call):

    if not is_admin(call.from_user.id):
        return

    if call.data == "maintenance_on":
        settings["maintenance"] = True
        save_settings(settings)
        backup_settings()

        bot.edit_message_text(
            "🟢 Maintenance Enabled",
            call.message.chat.id,
            call.message.message_id
        )

    elif call.data == "maintenance_off":
        settings["maintenance"] = False
        save_settings(settings)
        backup_settings()

        bot.edit_message_text(
            "🔴 Maintenance Disabled",
            call.message.chat.id,
            call.message.message_id
        )


# ===============================
# CURSOR YAHI CHHOD DENA
# PART 6B-2 YAHIN SE START HOGA
# ===============================
