import telebot

TOKEN = "TU_WSTAW_TOKEN"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

BAD_WORDS = [
    # POLSKIE
    "k***a", "p***ć", "j***ć", "ch***j", "h***j", "s***ć", "w***r", "p***r",
    "d***l", "i***a", "d***a", "s***n", "p***s", "p***z", "r***ć", "z***ć",
    "o***r", "g***w", "g***wno", "g***wniany", "s***syn", "s***fi", "s***fiarz",
    "s***fiara", "s***fiak", "s***fiara", "s***fić", "s***fiło", "s***fiłeś",
    "s***fiłam", "s***fiłem",

    # ANGLIELSKIE
    "f**k", "f***ing", "f***er", "f***ed", "f***s", "f***koff",
    "s**t", "s***ty", "s***head", "s***bag",
    "b***h", "b***hes",
    "a**hole", "a**holes",
    "d***head", "d***heads",
    "c**t", "c***s",
    "m***erf***er", "m***erf***ing",
    "w***e", "w***res",
    "b***tard", "b***tards",

    # LITERÓWKI / OMIJANE FILTRY
    "k u r w a", "k.u.r.w.a", "kurw@", "kvrwa", "k*rwa",
    "f u c k", "f.u.c.k", "fu*k", "fck", "fuk",
    "s h i t", "sh1t", "sh*t",
    "b i t c h", "b1tch", "b*tch",
]

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Cześć! Jestem botem moderatorem.\n"
        "Dodaj mnie do grupy i nadaj mi uprawnienia admina."
    )

@bot.message_handler(func=lambda m: True)
def moderation(message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    text = (message.text or "").lower()

    if any(bad.replace("*", "") in text.replace("*", "") for bad in BAD_WORDS):
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

        bot.send_message(
            message.chat.id,
            f"{message.from_user.first_name}, Twoja wiadomość została usunięta."
        )

bot.infinity_polling()
