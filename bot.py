import re
from datetime import datetime, timedelta
import telebot
from telebot import types

# ==========================
# KONFIGURACJA
# ==========================

TOKEN = "TU_WSTAW_TOKEN"
LOG_CHANNEL_ID = -1000000000000  # ID kanału logów (np. -1001234567890)

bot = telebot.TeleBot(TOKEN)

# ==========================
# WARNY (w pamięci)
# ==========================

warns_db = {}  # {chat_id: {user_id: warns_count}}

def add_warn(chat_id, user_id):
    if chat_id not in warns_db:
        warns_db[chat_id] = {}
    warns_db[chat_id][user_id] = warns_db[chat_id].get(user_id, 0) + 1
    return warns_db[chat_id][user_id]

def reset_warns(chat_id, user_id):
    if chat_id in warns_db and user_id in warns_db[chat_id]:
        warns_db[chat_id][user_id] = 0

# ==========================
# LOGI
# ==========================

def log_event(text):
    try:
        bot.send_message(LOG_CHANNEL_ID, text)
    except Exception:
        pass

# ==========================
# MUTE / BAN
# ==========================

def mute_user(chat_id, user_id, seconds, reason):
    until = datetime.now() + timedelta(seconds=seconds)
    try:
        bot.restrict_chat_member(chat_id, user_id, until_date=until)
        log_event(f"🔇 MUTE: user_id={user_id}, chat_id={chat_id}, seconds={seconds}, reason={reason}")
    except Exception as e:
        log_event(f"❌ MUTE ERROR: {e}")

def ban_user(chat_id, user_id, reason):
    try:
        bot.ban_chat_member(chat_id, user_id)
        log_event(f"⛔ BAN: user_id={user_id}, chat_id={chat_id}, reason={reason}")
    except Exception as e:
        log_event(f"❌ BAN ERROR: {e}")

# ==========================
# FILTR PRO PRZEKLEŃSTW
# ==========================

# rdzenie słów (bez odmian)
BAD_ROOTS = [
    "kurw", "chuj", "pizd", "jeb", "pierdol", "skurw", "suka", "dziwk",
    "fiut", "huj", "kutas", "sperma", "sra", "srak", "gówno", "gown"
]

# zamiany liter (leet / podobne)
LEET_MAP = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
    "!": "i",
    "*": "",
}

def normalize_text(text: str) -> str:
    # małe litery
    t = text.lower()

    # usuń spacje między literami (k u r w a -> kurwa)
    t = re.sub(r"\s+", "", t)

    # usuń znaki interpunkcyjne
    t = re.sub(r"[.,;:!?()

\[\]

{}<>\"']", "", t)

    # zamień leet
    for k, v in LEET_MAP.items():
        t = t.replace(k, v)

    return t

def contains_bad_word(text: str) -> bool:
    norm = normalize_text(text)
    for root in BAD_ROOTS:
        if root in norm:
            return True
    return False

# ==========================
# BLOKADA LINKÓW / MEDIÓW (opcjonalnie)
# ==========================

def contains_link(text: str) -> bool:
    if not text:
        return False
    return any(x in text.lower() for x in ["http://", "https://", "t.me/", ".com", ".ru", ".pl"])

# ==========================
# GŁÓWNY FILTR WIADOMOŚCI
# ==========================

@bot.message_handler(func=lambda m: True, content_types=['text'])
def main_filter(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text or ""

    # ignoruj własne logi / kanały
    if message.chat.type not in ["group", "supergroup"]:
        return

    # FILTR PRZEKLEŃSTW PRO
    if contains_bad_word(text):
        warns = add_warn(chat_id, user_id)

        if warns >= 5:
            ban_user(chat_id, user_id, "5+ warnów za przekleństwa")
            bot.send_message(chat_id, f"{message.from_user.first_name} został zbanowany za ciężkie przekleństwa.")
            return

        if warns == 1:
            bot.send_message(chat_id, f"{message.from_user.first_name}, ostrzeżenie (1/3).")
            log_event(f"⚠️ WARN 1: user_id={user_id}, chat_id={chat_id}, text={text}")
        elif warns == 2:
            bot.send_message(chat_id, f"{message.from_user.first_name}, ostrzeżenie (2/3).")
            log_event(f"⚠️ WARN 2: user_id={user_id}, chat_id={chat_id}, text={text}")
        elif warns == 3:
            mute_user(chat_id, user_id, 600, "3 warny => mute 10 min")
            bot.send_message(chat_id, f"{message.from_user.first_name} został wyciszony na 10 minut (3 warny).")
        elif warns == 4:
            mute_user(chat_id, user_id, 3600, "4 warny => mute 1h")
            bot.send_message(chat_id, f"{message.from_user.first_name} został wyciszony na 1 godzinę (4 warny).")
        else:
            mute_user(chat_id, user_id, 86400, "5+ warnów => mute 24h")
            bot.send_message(chat_id, f"{message.from_user.first_name} został wyciszony na 24 godziny (5+ warnów).")

        log_event(f"⚠️ MUTE BY WARNS: user_id={user_id}, chat_id={chat_id}, warns={warns}, text={text}")
        return

    # BLOKADA LINKÓW (opcjonalnie)
    if contains_link(text):
        bot.delete_message(chat_id, message.message_id)
        log_event(f"🔗 LINK BLOCKED: user_id={user_id}, chat_id={chat_id}, text={text}")
        return

# ==========================
# /start
# ==========================

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Cześć! Jestem AxelBot MAX (PRO).\n"
        "- filtr przekleństw PRO (odmiany, leet, spacje)\n"
        "- warny, mute, ban\n"
        "- blokada linków\n"
        "- panel admina\n"
        "- logi do kanału adminów."
    )

# ==========================
# POMOCNICZE: sprawdzanie admina
# ==========================

def is_admin(bot_obj, chat_id, user_id):
    try:
        member = bot_obj.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception:
        return False

# ==========================
# PANEL ADMINA (/panel)
# ==========================

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
        types.InlineKeyboardButton("🔇 Mute 10m", callback_data="admin_mute_10"),
        types.InlineKeyboardButton("🔇 Mute 1h", callback_data="admin_mute_60"),
    )
    kb.add(
        types.InlineKeyboardButton("🔇 Mute 24h", callback_data="admin_mute_1440"),
        types.InlineKeyboardButton("⛔ Ban", callback_data="admin_ban")
    )
    kb.add(
        types.InlineKeyboardButton("📜 Logi", callback_data="admin_logs")
    )

    bot.reply_to(message, "🔧 <b>Admin Panel</b>\nWybierz akcję:", reply_markup=kb, parse_mode="HTML")

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
    data = callback.data

    if data == "admin_warn":
        warns = add_warn(chat_id, target)
        bot.send_message(chat_id, f"⚠️ Warn dodany. Użytkownik ma {warns} warnów.")
        log_event(f"⚠️ ADMIN WARN: target={target}, chat_id={chat_id}, warns={warns}")
        bot.answer_callback_query(callback.id, "Warn dodany.")

    elif data == "admin_unwarn":
        reset_warns(chat_id, target)
        bot.send_message(chat_id, "♻️ Warny wyzerowane.")
        log_event(f"♻️ ADMIN UNWARN: target={target}, chat_id={chat_id}")
        bot.answer_callback_query(callback.id, "Warny wyzerowane.")

    elif data.startswith("admin_mute_"):
        minutes = int(data.split("_")[2])
        seconds = minutes * 60
        mute_user(chat_id, target, seconds, f"Admin mute {minutes}m")
        bot.send_message(chat_id, f"🔇 Użytkownik wyciszony na {minutes} minut.")
        bot.answer_callback_query(callback.id, f"Mute {minutes}m.")

    elif data == "admin_ban":
        ban_user(chat_id, target, "Admin ban")
        bot.send_message(chat_id, "⛔ Użytkownik zbanowany.")
        bot.answer_callback_query(callback.id, "Ban wykonany.")

    elif data == "admin_logs":
        bot.send_message(chat_id, f"📜 Logi wysyłane do kanału:\n<code>{LOG_CHANNEL_ID}</code>", parse_mode="HTML")
        bot.answer_callback_query(callback.id, "Informacja o logach.")

# ==========================
# START BOTA
# ==========================

bot.infinity_polling()
