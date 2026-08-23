import telebot
from telebot import types
from datetime import datetime, timedelta

TOKEN = "8942399382:AAH8s0mcxBRk26IHGzc7mepheWkw3szrOEs"
LOG_CHANNEL_ID = ID: -1004410834577  # Twój kanał logów

bot = telebot.TeleBot(TOKEN)

# ==========================
# WARNY + BAZA W PAMIĘCI
# ==========================

warns_db = {}

def add_warn(chat_id, user_id):
    if chat_id not in warns_db:
        warns_db[chat_id] = {}
    warns_db[chat_id][user_id] = warns_db[chat_id].get(user_id, 0) + 1
    return warns_db[chat_id][user_id]

def reset_warns(chat_id, user_id):
    if chat_id in warns_db and user_id in warns_db[chat_id]:
        warns_db[chat_id][user_id] = 0

# ==========================
# MUTE / BAN
# ==========================

def mute_user(chat_id, user_id, seconds, reason):
    until = datetime.now() + timedelta(seconds=seconds)
    bot.restrict_chat_member(chat_id, user_id, until_date=until)
    log_event(f"🔇 MUTE: {user_id} na {seconds}s | {reason}")

def ban_user(chat_id, user_id, reason):
    bot.ban_chat_member(chat_id, user_id)
    log_event(f"⛔ BAN: {user_id} | {reason}")

# ==========================
# LOGI
# ==========================

def log_event(text):
    try:
        bot.send_message(LOG_CHANNEL_ID, text)
    except:
        pass

# ==========================
# FILTR PRZEKLEŃSTW
# ==========================

bad_words = ["kurwa", "chuj", "pizda", "jebany", "jebać", "pierdol"]

@bot.message_handler(func=lambda m: True)
def filter_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.lower()

    if any(bad in text for bad in bad_words):
        warns = add_warn(chat_id, user_id)

        if warns >= 5:
            ban_user(chat_id, user_id, "Ciężkie przekleństwa")
            bot.send_message(chat_id, f"{message.from_user.first_name} został zbanowany.")
            return

        if warns == 1:
            bot.send_message(chat_id, f"{message.from_user.first_name}, ostrzeżenie (1/3).")
        elif warns == 2:
            bot.send_message(chat_id, f"{message.from_user.first_name}, ostrzeżenie (2/3).")
        elif warns == 3:
            mute_user(chat_id, user_id, 600, "3 warny => mute 10 min")
            bot.send_message(chat_id, f"{message.from_user.first_name} wyciszony na 10 minut.")
        elif warns == 4:
            mute_user(chat_id, user_id, 3600, "4 warny => mute 1h")
            bot.send_message(chat_id, f"{message.from_user.first_name} wyciszony na 1 godzinę.")
        else:
            mute_user(chat_id, user_id, 86400, "5+ warnów => mute 24h")
            bot.send_message(chat_id, f"{message.from_user.first_name} wyciszony na 24h.")

        log_event(f"⚠️ WARN/MUTE: {user_id} | {warns} warnów | {text}")

# ==========================
# START
# ==========================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Cześć! Jestem AxelBot MAX.\n"
        "- filtr przekleństw\n"
        "- warny, mute, ban\n"
        "- blokada linków\n"
        "- CAPTCHA\n"
        "- panel admina\n"
        "- logi do kanału"
    )

# ==========================
# PANEL ADMINA (POŁĄCZONY)
# ==========================

def is_admin(bot, chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

@bot.message_handler(commands=['panel'])
def admin_panel(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not is_admin(bot, chat_id, user_id):
        bot.reply_to(message, "❌ Panel tylko dla adminów.")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ Panel działa tylko na odpowiedź na wiadomość.")
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("⚠️ Warn", callback_data="admin_warn"),
        types.InlineKeyboardButton("♻️ Unwarn", callback_data="admin_unwarn")
    )
    kb.add(
        types.InlineKeyboardButton("🔇 Mute", callback_data="admin_mute"),
        types.InlineKeyboardButton("⛔ Ban", callback_data="admin_ban")
    )
    kb.add(
        types.InlineKeyboardButton("📜 Logi", callback_data="admin_logs")
    )

    bot.reply_to(message, "🔧 <b>Admin Panel</b>\nWybierz akcję:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_"))
def admin_actions(callback):
    chat_id = callback.message.chat.id
    admin_id = callback.from_user.id

    if not is_admin(bot, chat_id, admin_id):
        bot.answer_callback_query(callback.id, "❌ Nie jesteś adminem.")
        return

    if not callback.message.reply_to_message:
        bot.answer_callback_query(callback.id, "⚠️ Panel działa tylko na odpowiedź.")
        return

    target = callback.message.reply_to_message.from_user.id
    action = callback.data.split("_")[1]

    if action == "warn":
        warns = add_warn(chat_id, target)
        bot.send_message(chat_id, f"⚠️ Warn dodany. Użytkownik ma {warns}/3.")
        bot.answer_callback_query(callback.id, "Warn dodany.")

    elif action == "unwarn":
        reset_warns(chat_id, target)
        bot.send_message(chat_id, "♻️ Warny wyzerowane.")
        bot.answer_callback_query(callback.id, "Warny wyzerowane.")

    elif action == "mute":
        mute_user(chat_id, target, 600, "Admin mute 10m")
        bot.send_message(chat_id, "🔇 Użytkownik wyciszony na 10 minut.")
        bot.answer_callback_query(callback.id, "Mute 10m.")

    elif action == "ban":
        ban_user(chat_id, target, "Admin ban")
        bot.send_message(chat_id, "⛔ Użytkownik zbanowany.")
        bot.answer_callback_query(callback.id, "Ban wykonany.")

    elif action == "logs":
        bot.send_message(chat_id, f"📜 Logi wysyłane do:\n<code>{LOG_CHANNEL_ID}</code>")
        bot.answer_callback_query(callback.id, "Logi wysłane.")

# ==========================
# START BOTA
# ==========================

bot.infinity_polling()
