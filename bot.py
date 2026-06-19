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
# ======================================
# PART 6B-2A
# BROADCAST SYSTEM (STEP 1)
# ======================================

broadcast_data = {
    "mode": None,
    "button_text": None,
    "button_url": None,
    "message": None,
    "photo": None,
    "forward": None
}

waiting_broadcast = {}

# ----------------------------
# Broadcast Menu
# ----------------------------

@bot.message_handler(func=lambda m: m.text == "📢 Broadcast")
def broadcast_menu(message):

    if not admin_only(message):
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row("📝 Text Broadcast", "🖼 Photo Broadcast")
    markup.row("📨 Forward Broadcast")
    markup.row("❌ Cancel Broadcast")

    bot.send_message(
        message.chat.id,
        "📢 <b>Broadcast Panel</b>\n\n"
        "Select broadcast type.",
        parse_mode="HTML",
        reply_markup=markup
    )


# ----------------------------
# Cancel Broadcast
# ----------------------------

@bot.message_handler(func=lambda m: m.text == "❌ Cancel Broadcast")
def cancel_broadcast(message):

    if not admin_only(message):
        return

    waiting_broadcast.clear()

    bot.send_message(
        message.chat.id,
        "❌ Broadcast Cancelled.",
        reply_markup=admin_keyboard()
    )


# ----------------------------
# Text Broadcast
# ----------------------------

@bot.message_handler(func=lambda m: m.text == "📝 Text Broadcast")
def text_broadcast(message):

    if not admin_only(message):
        return

    waiting_broadcast[message.from_user.id] = "text"

    bot.send_message(
        message.chat.id,
        "📝 Send the broadcast text."
    )


# ----------------------------
# Photo Broadcast
# ----------------------------

@bot.message_handler(func=lambda m: m.text == "🖼 Photo Broadcast")
def photo_broadcast(message):

    if not admin_only(message):
        return

    waiting_broadcast[message.from_user.id] = "photo"

    bot.send_message(
        message.chat.id,
        "🖼 Send photo with caption."
    )


# ----------------------------
# Forward Broadcast
# ----------------------------

@bot.message_handler(func=lambda m: m.text == "📨 Forward Broadcast")
def forward_broadcast(message):

    if not admin_only(message):
        return

    waiting_broadcast[message.from_user.id] = "forward"

    bot.send_message(
        message.chat.id,
        "📨 Forward any message."
    )# ======================================
# PART 6B-2B
# CONTINUE FROM HERE (PASTE BELOW LINE 539)
# ======================================

@bot.message_handler(func=lambda m: waiting_broadcast.get(m.from_user.id) == "text", content_types=["text"])
def receive_text_broadcast(message):

    if not admin_only(message):
        return

    broadcast_data["mode"] = "text"
    broadcast_data["message"] = message.text

    waiting_broadcast[message.from_user.id] = "button_text"

    bot.send_message(
        message.chat.id,
        "🔘 Send Register Button Text."
    )


@bot.message_handler(func=lambda m: waiting_broadcast.get(m.from_user.id) == "button_text", content_types=["text"])
def receive_button_text(message):

    if not admin_only(message):
        return

    broadcast_data["button_text"] = message.text

    waiting_broadcast[message.from_user.id] = "button_url"

    bot.send_message(
        message.chat.id,
        "🌐 Send Register Button Link."
    )


@bot.message_handler(func=lambda m: waiting_broadcast.get(m.from_user.id) == "button_url", content_types=["text"])
def receive_button_url(message):

    if not admin_only(message):
        return

    broadcast_data["button_url"] = message.text

    waiting_broadcast.pop(message.from_user.id, None)

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "✅ Start Broadcast",
            callback_data="start_broadcast"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "❌ Cancel",
            callback_data="cancel_final_broadcast"
        )
    )

    bot.send_message(
        message.chat.id,
        "✅ Broadcast Ready.\n\nPress Start Broadcast.",
        reply_markup=markup
    )# =====================================
# PART 6B-2C
# START BROADCAST CALLBACK
# =====================================

@bot.callback_query_handler(func=lambda c: c.data == "cancel_final_broadcast")
def cancel_final_broadcast(call):

    if not is_admin(call.from_user.id):
        return

    waiting_broadcast.pop(call.from_user.id, None)

    broadcast_data["mode"] = None
    broadcast_data["button_text"] = None
    broadcast_data["button_url"] = None
    broadcast_data["message"] = None
    broadcast_data["photo"] = None
    broadcast_data["forward"] = None

    bot.edit_message_text(
        "❌ Broadcast Cancelled.",
        call.message.chat.id,
        call.message.message_id
    )


@bot.callback_query_handler(func=lambda c: c.data == "start_broadcast")
def start_broadcast_callback(call):

    if not is_admin(call.from_user.id):
        return

    sent = 0
    failed = 0

    markup = None

    if broadcast_data["button_text"] and broadcast_data["button_url"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                broadcast_data["button_text"],
                url=broadcast_data["button_url"]
            )
        )

    users = load_users()

    for uid in users:

        try:

            if broadcast_data["mode"] == "text":

                bot.send_message(
                    uid,
                    broadcast_data["message"],
                    parse_mode="HTML",
                    reply_markup=markup
                )

            elif broadcast_data["mode"] == "photo":

                bot.send_photo(
                    uid,
                    broadcast_data["photo"],
                    caption=broadcast_data["message"],
                    parse_mode="HTML",
                    reply_markup=markup
                )

            elif broadcast_data["mode"] == "forward":

                bot.forward_message(
                    uid,
                    broadcast_data["forward"].chat.id,
                    broadcast_data["forward"].message_id
                )

            sent += 1

        except:
            failed += 1

    bot.edit_message_text(
        f"""✅ <b>Broadcast Completed Successfully</b>

👥 Total Users      : {len(users)}
✅ Successfully Sent: {sent}
❌ Failed           : {failed}

━━━━━━━━━━━━━━━━━━
📊 Live Analytics
👆 Register Clicks : 0
📈 Click Rate      : 0%
━━━━━━━━━━━━━━━━━━

🕒 Last Click : --
🔄 Status     : LIVE""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )

    broadcast_data["mode"] = None
    broadcast_data["button_text"] = None
    broadcast_data["button_url"] = None
    broadcast_data["message"] = None
    broadcast_data["photo"] = None
    broadcast_data["forward"] = None# =====================================
# PART 6B-2D
# LIVE CLICK TRACKING
# =====================================

click_stats = {
    "total_clicks": 0,
    "last_click": "--"
}


def register_click(user_id):
    global click_stats

    click_stats["total_clicks"] += 1
    click_stats["last_click"] = time.strftime("%d-%m-%Y %H:%M:%S")

    try:
        with open("click_stats.json", "w") as f:
            json.dump(click_stats, f, indent=4)
    except:
        pass


try:
    with open("click_stats.json", "r") as f:
        click_stats = json.load(f)
except:
    pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("register_click"))
def register_click_callback(call):

    register_click(call.from_user.id)

    bot.answer_callback_query(
        call.id,
        "✅ Registered Successfully!"
    )# =====================================
# PART 6B-2E
# REGISTER BUTTON + LIVE COUNT
# =====================================

broadcast_clicks = {}

def create_register_markup(post_id, text, url):
    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            text,
            callback_data=f"register_{post_id}"
        )
    )

    markup.add(
        types.InlineKeyboardButton(
            "🌐 Open Link",
            url=url
        )
    )

    return markup


@bot.callback_query_handler(func=lambda c: c.data.startswith("register_"))
def register_button_clicked(call):

    post_id = call.data.split("_", 1)[1]

    if post_id not in broadcast_clicks:
        broadcast_clicks[post_id] = {
            "clicks": 0,
            "users": []
        }

    if call.from_user.id not in broadcast_clicks[post_id]["users"]:
        broadcast_clicks[post_id]["users"].append(call.from_user.id)
        broadcast_clicks[post_id]["clicks"] += 1

    register_click(call.from_user.id)

    bot.answer_callback_query(
        call.id,
        "✅ Click Recorded Successfully!"
    )# =====================================
# PART 6B-2F
# SAVE CLICK DATA
# =====================================

def save_clicks():
    try:
        with open("broadcast_clicks.json", "w") as f:
            json.dump(broadcast_clicks, f, indent=4)
    except:
        pass


def load_clicks():
    global broadcast_clicks

    try:
        with open("broadcast_clicks.json", "r") as f:
            broadcast_clicks = json.load(f)
    except:
        broadcast_clicks = {}


load_clicks()


def get_post_clicks(post_id):
    if post_id in broadcast_clicks:
        return broadcast_clicks[post_id]["clicks"]
    return 0


def get_click_rate(post_id, total_users):
    if total_users == 0:
        return 0

    return round(
        (get_post_clicks(post_id) / total_users) * 100,
        2
    )# =====================================
# PART 6B-2G
# UPDATE LIVE ANALYTICS
# =====================================

def update_live_report(
    chat_id,
    message_id,
    post_id,
    total_users,
    sent,
    failed
):

    clicks = get_post_clicks(post_id)
    rate = get_click_rate(post_id, total_users)

    try:
        bot.edit_message_text(
            f"""✅ <b>Broadcast Completed Successfully</b>

👥 Total Users      : {total_users}
✅ Successfully Sent: {sent}
❌ Failed           : {failed}

━━━━━━━━━━━━━━━━━━
📊 <b>Live Analytics</b>

👆 Register Clicks : {clicks}
📈 Click Rate      : {rate}%

━━━━━━━━━━━━━━━━━━

🕒 Last Click : {click_stats['last_click']}
🔄 Status     : LIVE
""",
            chat_id,
            message_id,
            parse_mode="HTML"
        )
    except:
        pass# =================================
# PART 6B-2H
# RESET LIVE ANALYTICS
# =================================

def reset_click_stats():
    global click_stats
    global broadcast_clicks

    click_stats = {
        "total_clicks": 0,
        "last_click": "--"
    }

    broadcast_clicks = {}

    try:
        with open("click_stats.json", "w") as f:
            json.dump(click_stats, f, indent=4)

        with open("broadcast_clicks.json", "w") as f:
            json.dump(broadcast_clicks, f, indent=4)
    except:
        pass


def new_post_id():
    return str(int(time.time()))


def prepare_live_post():
    post_id = new_post_id()

    broadcast_clicks[post_id] = {
        "clicks": 0,
        "users": []
    }

    save_clicks()

    return post_id# =================================
# PART 6B-2I
# BROADCAST FINAL HELPERS
# =================================

def clear_broadcast():
    global broadcast_data

    broadcast_data["mode"] = None
    broadcast_data["button_text"] = None
    broadcast_data["button_url"] = None
    broadcast_data["message"] = None
    broadcast_data["photo"] = None
    broadcast_data["forward"] = None


def get_live_stats(post_id):
    clicks = get_post_clicks(post_id)
    rate = get_click_rate(post_id, get_total_users())

    return {
        "clicks": clicks,
        "rate": rate,
        "last_click": click_stats.get("last_click", "--")
    }# =================================
# PART 6B-2J
# SAVE LIVE REPORT
# =================================

def save_live_report(post_id):
    save_clicks()

    try:
        with open("live_post.json", "w") as f:
            json.dump({
                "post_id": post_id,
                "clicks": get_post_clicks(post_id),
                "rate": get_click_rate(post_id, get_total_users()),
                "last_click": click_stats.get("last_click", "--")
            }, f, indent=4)
    except:
        pass


def load_live_report():
    try:
        with open("live_post.json", "r") as f:
            return json.load(f)
    except:
        return None# =================================
# PART 6B-2K
# LIVE REPORT REFRESH
# =================================

def refresh_live_report(chat_id, message_id, post_id):
    stats = get_live_stats(post_id)

    try:
        bot.edit_message_text(
            f"""✅ <b>Broadcast Live Report</b>

👥 Total Clicks : <b>{stats['clicks']}</b>
📈 Click Rate : <b>{stats['rate']}%</b>

🕒 Last Click : <b>{stats['last_click']}</b>
🟢 Status : <b>LIVE</b>
""",
            chat_id,
            message_id,
            parse_mode="HTML"
        )
    except:
        pass# =================================
# PART 6B-2L
# AUTO UPDATE LIVE REPORT
# =================================

def update_live_report(
    chat_id,
    message_id,
    post_id,
    interval=10
):
    try:
        report = load_live_report()

        if not report:
            return

        if report["post_id"] != post_id:
            return

        refresh_live_report(
            chat_id,
            message_id,
            post_id
        )

    except:
        pass# =================================
# PART 6B-2M
# AUTO REFRESH WRAPPER
# =================================

def auto_refresh_live(chat_id, message_id, post_id):
    try:
        report = load_live_report()

        if not report:
            return

        if report.get("post_id") != post_id:
            return

        refresh_live_report(
            chat_id,
            message_id,
            post_id
        )

        save_live_report(post_id)

    except:
        pass# =================================
# PART 6B-2N
# FINAL LIVE UPDATE CALL
# =================================

def update_dashboard(chat_id, message_id, post_id):
    try:
        auto_refresh_live(
            chat_id,
            message_id,
            post_id
        )

        refresh_live_report(
            chat_id,
            message_id,
            post_id
        )

    except:
        pass# =================================
# PART 6B-2O
# RUN LIVE DASHBOARD
# =================================

def start_live_dashboard(chat_id, message_id, post_id):
    try:
        update_dashboard(
            chat_id,
            message_id,
            post_id
        )

    except:
        pass# =================================
# PART 6B-2P
# START DASHBOARD AFTER BROADCAST
# =================================

def launch_live_dashboard(chat_id, message_id, post_id):
    try:
        start_live_dashboard(
            chat_id,
            message_id,
            post_id
        )
    except:
        pass
