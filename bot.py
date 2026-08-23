import telebot
from telebot import types
import re
import time

TOKEN = "8942399382:AAH8s0mcxBRk26IHGzc7mepheWkw3szrOEs"  # <-- tutaj wstaw swój prawdziwy token
LOG_CHANNEL_ID = -1004410834577  # kanał logów adminów

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ====== FILTR PRZEKLEŃSTW (MAX, OCENZUROWANY) ======
BAD_WORDS = [
    # POLSKIE (ocenzurowane)
    "k***a", "p***ć", "j***ć", "ch***j", "h***j", "s***ć", "w***r", "p***r",
    "d***l", "i***a", "d***a", "s***n", "p***s", "p***z", "r***ć", "z***ć",
    "o***r", "g***w", "g***wno", "g***wniany", "s***syn",

    # ANGIELSKIE (ocenzurowane)
    "f**k", "f***ing", "f***er", "f***ed", "f***s", "f***off",
    "s**t", "s***ty", "s***head", "s***bag",
    "b***h", "b***hes",
    "a**hole", "a**holes",
    "d***head", "d***heads",
    "c**t", "c***s",
    "m***erf***er", "m***erf***ing",
    "w***e", "w***res",
    "b***tard", "b***tards",

    # ROSYJSKIE / UKRAIŃSKIE / NIEMIECKIE (ocenzurowane)
    "h***й", "п***да", "е***ть", "б***ть", "с***ка", "м***да", "г***но",
    "s***e", "a***ch", "h***re", "m***st", "v***rdammt",
    "х***й",

    # LITERÓWKI / OMIJANIE FILTRÓW
    "k u r w a", "k.u.r.w.a", "kurw@", "kvrwa", "k*rwa",
    "f u c k", "f.u.c.k", "fu*k", "fck", "fuk",
    "s h i t", "sh1t", "sh*t",
    "b i t c h", "b1tch", "b*tch",
]

HEAVY_BAD_WORDS = [
    # cięższe przekleństwa (ocenzurowane) → ban
    "k***a", "j***ć", "ch***j", "m***erf***er", "c**t"
]

def normalize_text(text: str) -> str:
    cleaned = text.lower()
    cleaned = cleaned.replace("*", "").replace(".", "").replace(" ", "")
    cleaned = cleaned.replace("1", "i").replace("3", "e").replace("4", "a").replace("0", "o")
    return cleaned

def contains_bad_word(text: str) -> bool:
    cleaned = normalize_text(text)
    for bad in BAD_WORDS:
        bad_clean = normalize_text(bad)
        if bad_clean in cleaned:
            return True
    return False

def contains_heavy_bad_word(text: str) -> bool:
    cleaned = normalize_text(text)
    for bad in HEAVY_BAD_WORDS:
        bad_clean = normalize_text(bad)
        if bad_clean in cleaned:
            return True
    return False

# ====== WARNY / MUTE / BAN ======
user_warns = {}  # {chat_id: {user_id: warn_count}}

MUTE_10_MIN = 10 * 60
MUTE_1_H = 60 * 60
MUTE_24_H = 24 * 60 * 60

def add_warn(chat_id: int, user_id: int) -> int:
    if chat_id not in user_warns:
        user_warns[chat_id] = {}
    user_warns[chat_id][user_id] = user_warns[chat_id].get(user_id, 0) + 1
    return user_warns[chat_id][user_id]

def reset_warns(chat_id: int, user_id: int):
    if chat_id in user_warns and user_id in user_warns[chat_id]:
        user_warns[chat_id][user_id] = 0

def log_event(text: str):
    try:
        bot.send_message(LOG_CHANNEL_ID, text)
    except:
        pass

def mute_user(chat_id: int, user_id: int, seconds: int, reason: str):
    until_date = int(time.time()) + seconds
    try:
        bot.restrict_chat_member(
            chat_id,
            user_id,
            until_date=until_date,
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        log_event(f"🔇 MUTE: user_id={user_id}, chat_id={chat_id}, seconds={seconds}, reason={reason}")
    except Exception as e:
        log_event(f"❗ MUTE FAILED: user_id={user_id}, chat_id={chat_id}, error={e}")

def ban_user(chat_id: int, user_id: int, reason: str):
    try:
        bot.ban_chat_member(chat_id, user_id)
        log_event(f"⛔ BAN: user_id={user_id}, chat_id={chat_id}, reason={reason}")
    except Exception as e:
        log_event(f"❗ BAN FAILED: user_id={user_id}, chat_id={chat_id}, error={e}")

# ====== BLOKOWANIE LINKÓW / MEDIÓW ======
def contains_link(text: str) -> bool:
    if not text:
        return False
    pattern = r"(https?://|t\.me/|telegram\.me|www\.)"
    return re.search(pattern, text.lower()) is not None

def is_media(message) -> bool:
    return bool(message.photo or message.video or message.document or message.animation or message.audio or message.voice)

# ====== CAPTCHA EMOJI DLA NOWYCH UŻYTKOWNIKÓW ======
pending_captcha = {}  # {chat_id: {user_id: True}}

CAPTCHA_EMOJI = "🚀"

@bot.message_handler(content_types=['new_chat_members'])
def on_new_member(message):
    chat_id = message.chat.id
    for user in message.new_chat_members:
        user_id = user.id

        try:
            bot.restrict_chat_member(
                chat_id,
                user_id,
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        except:
            pass

        pending_captcha.setdefault(chat_id, {})[user_id] = True

        kb = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton(text=CAPTCHA_EMOJI, callback_data=f"captcha_ok:{user_id}")
        kb.add(btn)

        bot.send_message(
            chat_id,
            f"👋 Witaj, <b>{user.first_name}</b>!\n\n"
            f"Aby pisać na tej grupie, kliknij przycisk {CAPTCHA_EMOJI} poniżej.",
            reply_markup=kb
        )

@bot.callback_query_handler(func=lambda c: c.data.startswith("captcha_ok:"))
def captcha_ok(callback_query):
    chat_id = callback_query.message.chat.id
    from_id = callback_query.from_user.id
    data_user_id = int(callback_query.data.split(":")[1])

    if from_id != data_user_id:
        bot.answer_callback_query(callback_query.id, "To nie jest Twoja CAPTCHA.")
        return

    if chat_id in pending_captcha and data_user_id in pending_captcha[chat_id]:
        del pending_captcha[chat_id][data_user_id]

        try:
            bot.restrict_chat_member(
                chat_id,
                data_user_id,
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        except:
            pass

        bot.answer_callback_query(callback_query.id, "✅ Zweryfikowano. Możesz pisać.")
        bot.send_message(chat_id, f"✅ <b>{callback_query.from_user.first_name}</b> przeszedł CAPTCHA.")
        log_event(f"✅ CAPTCHA OK: user_id={data_user_id}, chat_id={chat_id}")
    else:
        bot.answer_callback_query(callback_query.id, "CAPTCHA wygasła lub została już rozwiązana.")

# ====== GŁÓWNY MODERATOR ======
@bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'video', 'document', 'animation', 'audio', 'voice'])
def moderation(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text or ""

    if chat_id in pending_captcha and pending_captcha[chat_id].get(user_id):
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        bot.send_message(chat_id, f"⚠️ {message.from_user.first_name}, najpierw kliknij CAPTCHA, potem pisz.")
        log_event(f"⚠️ CAPTCHA BLOCK: user_id={user_id}, chat_id={chat_id}")
        return

    if contains_link(text):
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        add_warn(chat_id, user_id)
        bot.send_message(chat_id, f"🔗 {message.from_user.first_name}, linki są zablokowane.")
        log_event(f"🔗 LINK BLOCK: user_id={user_id}, chat_id={chat_id}, text={text}")
        return

    if is_media(message):
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass
        add_warn(chat_id, user_id)
        bot.send_message(chat_id, f"🖼️ {message.from_user.first_name}, media są zablokowane.")
        log_event(f"🖼️ MEDIA BLOCK: user_id={user_id}, chat_id={chat_id}")
        return

    if contains_bad_word(text):
        try:
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

        warns = add_warn(chat_id, user_id)

        if contains_heavy_bad_word(text):
            ban_user(chat_id, user_id, "Ciężkie przekleństwo")
            bot.send_message(chat_id, f"⛔ {message.from_user.first_name} został zbanowany za ciężkie przekleństwa.")
            return

        if warns == 1:
            bot.send_message(chat_id, f"⚠️ {message.from_user.first_name}, ostrzeżenie (1/3).")
            log_event(f"⚠️ WARN 1: user_id={user_id}, chat_id={chat_id}, text={text}")
        elif warns == 2:
            bot.send_message(chat_id, f"⚠️ {message.from_user.first_name}, ostrzeżenie (2/3).")
            log_event(f"⚠️ WARN 2: user_id={user_id}, chat_id={chat_id}, text={text}")
        elif warns >= 3:
            if warns == 3:
                mute_user(chat_id, user_id, MUTE_10_MIN, "3 warny → mute 10 min")
                bot.send_message(chat_id, f"🔇 {message.from_user.first_name} został wyciszony na 10 minut (3 warny).")
            elif warns == 4:
                mute_user(chat_id, user_id, MUTE_1_H, "4 warny → mute 1h")
                bot.send_message(chat_id, f"🔇 {message.from_user.first_name} został wyciszony na 1 godzinę (4 warny).")
            else:
                mute_user(chat_id, user_id, MUTE_24_H, "5+ warnów → mute 24h")
                bot.send_message(chat_id, f"🔇 {message.from_user.first_name} został wyciszony na 24 godziny (5+ warnów).")

            log_event(f"🔇 MUTE BY WARNS: user_id={user_id}, chat_id={chat_id}, warns={warns}, text={text}")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Cześć! Jestem <b>AxelBot MAX</b> moderator.\n"
        "- filtr przekleństw\n"
        "- warny, mute, ban\n"
        "- blokada linków i mediów\n"
        "- CAPTCHA emoji dla nowych użytkowników\n"
        "- logi do kanału adminów."
    )
from admin_panel import register_admin_panel

register_admin_panel(
    bot,
    LOG_CHANNEL_ID,
    add_warn,
    reset_warns,
    mute_user,
    ban_user
)

bot.infinity_polling()
