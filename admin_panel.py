from telebot import types

# ====== SUPER PRO ADMIN PANEL ======

# lokalna historia moderacji
moderation_history = {}  # {chat_id: [("admin", "target", "action")]}

# ustawienia grupy
group_settings = {}  # {chat_id: {"links": True, "media": True, "captcha": True, "antispam": True}}

def is_admin(bot, chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False


def register_admin_panel(bot, LOG_CHANNEL_ID, add_warn, reset_warns, mute_user, ban_user):

    # ====== PANEL KOMENDY ======
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
            types.InlineKeyboardButton("🔇 Mute", callback_data="admin_mute_menu"),
            types.InlineKeyboardButton("⛔ Ban", callback_data="admin_ban")
        )
        kb.add(
            types.InlineKeyboardButton("📊 Warny", callback_data="admin_warns"),
            types.InlineKeyboardButton("📜 Historia", callback_data="admin_history")
        )
        kb.add(
            types.InlineKeyboardButton("⚙️ Ustawienia", callback_data="admin_settings")
        )

        bot.reply_to(message, "🔧 <b>Admin Panel — SUPER PRO</b>\nWybierz akcję:", reply_markup=kb)

    # ====== CALLBACKI ======
    @bot.callback_query_handler(func=lambda c: c.data.startswith("admin_"))
    def admin_actions(callback):
        chat_id = callback.message.chat.id
        admin_id = callback.from_user.id

        if not is_admin(bot, chat_id, admin_id):
            bot.answer_callback_query(callback.id, "❌ Nie jesteś adminem.")
            return

        action = callback.data.split("_")[1]

        # ====== USTAWIENIA ======
        if action == "settings":
            kb = types.InlineKeyboardMarkup()

            settings = group_settings.setdefault(chat_id, {
                "links": True,
                "media": True,
                "captcha": True,
                "antispam": True
            })

            kb.add(
                types.InlineKeyboardButton(f"🔗 Linki: {'ON' if settings['links'] else 'OFF'}",
                                           callback_data="toggle_links"),
                types.InlineKeyboardButton(f"🖼️ Media: {'ON' if settings['media'] else 'OFF'}",
                                           callback_data="toggle_media")
            )
            kb.add(
                types.InlineKeyboardButton(f"🚀 Captcha: {'ON' if settings['captcha'] else 'OFF'}",
                                           callback_data="toggle_captcha"),
                types.InlineKeyboardButton(f"🛡️ Antyspam: {'ON' if settings['antispam'] else 'OFF'}",
                                           callback_data="toggle_antispam")
            )

            bot.edit_message_text(
                "⚙️ <b>Ustawienia grupy</b>\nKliknij, aby przełączyć:",
                chat_id,
                callback.message.message_id,
                reply_markup=kb
            )
            return

        # ====== TOGGLE ======
        if action in ["links", "media", "captcha", "antispam"]:
            settings = group_settings.setdefault(chat_id, {
                "links": True,
                "media": True,
                "captcha": True,
                "antispam": True
            })

            settings[action] = not settings[action]

            bot.answer_callback_query(callback.id, "Zmieniono ustawienie.")
            bot.send_message(chat_id, f"⚙️ {action.upper()} ustawione na: {settings[action]}")
            return

        # ====== HISTORIA ======
        if action == "history":
            history = moderation_history.get(chat_id, [])
            if not history:
                bot.answer_callback_query(callback.id, "Brak historii.")
                bot.send_message(chat_id, "📜 Brak historii moderacji.")
                return

            text = "📜 <b>Historia moderacji:</b>\n\n"
            for admin, target, act in history[-10:]:
                text += f"👮 {admin} → 👤 {target}: {act}\n"

            bot.send_message(chat_id, text)
            bot.answer_callback_query(callback.id, "Historia wyświetlona.")
            return

        # ====== WARNY ======
        if action == "warns":
            if not callback.message.reply_to_message:
                bot.answer_callback_query(callback.id, "⚠️ Odpowiedz na wiadomość użytkownika.")
                return

            target = callback.message.reply_to_message.from_user
            warns = add_warn(chat_id, target.id) - 1  # nie dodajemy nowego

            bot.send_message(chat_id, f"📊 Użytkownik <b>{target.first_name}</b> ma {warns}/3 warnów.")
            bot.answer_callback_query(callback.id, "Wyświetlono warny.")
            return

        # ====== MUTE MENU ======
        if action == "mute":
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("🔇 10 min", callback_data="mute_10"),
                types.InlineKeyboardButton("🔇 1 godz", callback_data="mute_60")
            )
            kb.add(
                types.InlineKeyboardButton("🔇 24 godz", callback_data="mute_1440")
            )

            bot.edit_message_text(
                "🔇 <b>Wybierz czas wyciszenia:</b>",
                chat_id,
                callback.message.message_id,
                reply_markup=kb
            )
            return

        # ====== MUTE CZASY ======
        if action in ["10", "60", "1440"]:
            if not callback.message.reply_to_message:
                bot.answer_callback_query(callback.id, "⚠️ Odpowiedz na wiadomość użytkownika.")
                return

            target = callback.message.reply_to_message.from_user
            minutes = int(action)
            seconds = minutes * 60

            mute_user(chat_id, target.id, seconds, f"Admin mute {minutes}m")
            bot.send_message(chat_id, f"🔇 Użytkownik wyciszony na {minutes} minut.")
            moderation_history.setdefault(chat_id, []).append(
                (admin_id, target.id, f"MUTE {minutes}m")
            )
            bot.answer_callback_query(callback.id, "Wyciszono.")
            return

        # ====== WARN ======
        if action == "warn":
            if not callback.message.reply_to_message:
                bot.answer_callback_query(callback.id, "⚠️ Odpowiedz na wiadomość.")
                return

            target = callback.message.reply_to_message.from_user
            warns = add_warn(chat_id, target.id)

            bot.send_message(chat_id, f"⚠️ Warn dodany. {warns}/3.")
            moderation_history.setdefault(chat_id, []).append(
                (admin_id, target.id, "WARN")
            )
            bot.answer_callback_query(callback.id, "Warn dodany.")
            return

        # ====== UNWARN ======
        if action == "unwarn":
            if not callback.message.reply_to_message:
                bot.answer_callback_query(callback.id, "⚠️ Odpowiedz na wiadomość.")
                return

            target = callback.message.reply_to_message.from_user
            reset_warns(chat_id, target.id)

            bot.send_message(chat_id, "♻️ Warny wyzerowane.")
            moderation_history.setdefault(chat_id, []).append(
                (admin_id, target.id, "UNWARN")
            )
            bot.answer_callback_query(callback.id, "Wyzerowano.")
            return

        # ====== BAN ======
        if action == "ban":
            if not callback.message.reply_to_message:
                bot.answer_callback_query(callback.id, "⚠️ Odpowiedz na wiadomość.")
                return

            target = callback.message.reply_to_message.from_user
            ban_user(chat_id, target.id, "Admin ban")

            bot.send_message(chat_id, "⛔ Użytkownik zbanowany.")
            moderation_history.setdefault(chat_id, []).append(
                (admin_id, target.id, "BAN")
            )
            bot.answer_callback_query(callback.id, "Ban wykonany.")
            return
