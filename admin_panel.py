from telebot import types

# ====== ADMIN PANEL (OSOBNY PLIK) ======

def is_admin(bot, chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False


def register_admin_panel(bot, LOG_CHANNEL_ID, add_warn, reset_warns, mute_user, ban_user):

    @bot.message_handler(commands=['panel'])
    def admin_panel(message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        if not is_admin(bot, chat_id, user_id):
            bot.reply_to(message, "❌ Panel tylko dla adminów.")
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

        action = callback.data.split("_")[1]

        if not callback.message.reply_to_message:
            bot.answer_callback_query(callback.id, "⚠️ Panel działa tylko na odpowiedź na wiadomość.")
            return

        target = callback.message.reply_to_message.from_user.id

        # WARN
        if action == "warn":
            warns = add_warn(chat_id, target)
            bot.send_message(chat_id, f"⚠️ Warn dodany. Użytkownik ma {warns}/3.")
            bot.answer_callback_query(callback.id, "Warn dodany.")

        # UNWARN
        elif action == "unwarn":
            reset_warns(chat_id, target)
            bot.send_message(chat_id, "♻️ Warny wyzerowane.")
            bot.answer_callback_query(callback.id, "Warny wyzerowane.")

        # MUTE
        elif action == "mute":
            mute_user(chat_id, target, 600, "Admin mute 10m")
            bot.send_message(chat_id, "🔇 Użytkownik wyciszony na 10 minut.")
            bot.answer_callback_query(callback.id, "Mute 10m.")

        # BAN
        elif action == "ban":
            ban_user(chat_id, target, "Admin ban")
            bot.send_message(chat_id, "⛔ Użytkownik zbanowany.")
            bot.answer_callback_query(callback.id, "Ban wykonany.")

        # LOGI
        elif action == "logs":
            bot.send_message(chat_id, f"📜 Logi są wysyłane do kanału:\n<code>{LOG_CHANNEL_ID}</code>")
            bot.answer_callback_query(callback.id, "Logi wysłane.")
