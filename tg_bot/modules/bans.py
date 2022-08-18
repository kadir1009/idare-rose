import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin, _TELE_GRAM_ID_S
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir",
    "Sohbet bulunamadı",
    "Sohbet üyesini kısıtlamak/kısıtlamayı kaldırmak için yeterli yetki yok",
    "User_not_participant",
    "Peer_id_invalid",
    "Grup sohbeti devre dışı bırakıldı",
    "Temel bir gruptan atmak için bir kullanıcının davetlisi olmanız gerekir",
    "Chat_admin_required",
    "Yalnızca grubun kurucusu grup yöneticilerini atabilir",
    "Channel_private",
    "Sohbette değil"
}

RUNBAN_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir",
    "Sohbet bulunamadı",
    "Sohbet üyesini kısıtlamak/kısıtlamayı kaldırmak için yeterli yetki yok",
    "User_not_participant",
    "Peer_id_invalid",
    "Grup sohbeti devre dışı bırakıldı",
    "Bir gruptan atmak için bir kullanıcının davetlisi olmanız gerekir",
    "Chat_admin_required",
    "Yalnızca  grubun kurucusu grup yöneticilerini atabilir",
    "Channel_private",
    "Sohbette değil"
}



@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if user.id not in _TELE_GRAM_ID_S:
        admin_user = chat.get_member(user.id)
        if not (
            admin_user.can_restrict_members or
            admin_user.status == "creator"
        ):
            return

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir kullanıcıdan bahsediyor gibi görünmüyorsun.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Keşke adminleri banlayabilsem...")
        return ""

    if user_id == bot.id:
        message.reply_text("Kendimi banlamayacağım, deli misin?")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Yönetici:</b> {}" \
          "\n<b>Kullanıcı:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Kural:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = "{} ന് ബണ്ണ് കൊടുത്തു വിട്ടിട്ടുണ്ട് !".format(mention_html(member.user.id, member.user.first_name))
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Cevaplanan mesaj bulunamadı":
            chat_id = update.effective_chat.id
            message = update.effective_message
            # Do not reply
            reply = "{} ന് ബണ്ണ് കൊടുത്തു വിട്ടിട്ടുണ്ട് !".format(mention_html(member.user.id, member.user.first_name))
            bot.send_message(chat_id, reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
#           message.reply_text('Banned!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("%s nedeniyle %s (%s) sohbetinde %s kullanıcısı yasaklamadı.", excp.message, chat.title, chat.id,
                             user_id)
            message.reply_text("O kullanıcıyı yasaklanamıyor.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if user.id not in _TELE_GRAM_ID_S:
        admin_user = chat.get_member(user.id)
        if not (
            admin_user.can_restrict_members or
            admin_user.status == "creator"
        ):
            return

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir kullanıcıdan bahsediyor gibi görünmüyorsun.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Keşke adminleri banlayabilseydim...")
        return ""

    if user_id == bot.id:
        message.reply_text("Kendimi banlamayacağım, deli misin?")
        return ""

    if not reason:
        message.reply_text("Bu kullanıcıyı yasaklamak için bir zaman belirlemediniz!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Yönetici:</b> {}" \
          "\n<b>Kullanıcı:</b> {}" \
          "\n<b>Zaman:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Sebep:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Banlandı! Kullanıcı yasaklanacak {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Cevaplanan mesaj bulunamadı":
            # Do not reply
            message.reply_text("Yasaklandı! Kullanıcı yasaklanacak {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("%s nedeniyle %s (%s) sohbetinde %s kullanıcısı yasaklamadı.", excp.message, chat.title, chat.id,
                             user_id)
            message.reply_text("O kullanıcıyı yasaklanamaz.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if user.id not in _TELE_GRAM_ID_S:
        admin_user = chat.get_member(user.id)
        if not (
            admin_user.can_restrict_members or
            admin_user.status == "creator"
        ):
            return

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Gerçekten adminleri atabilmeyi isterdim...")
        return ""

    if user_id == bot.id:
        message.reply_text("Evet, bunu yapmayacağım")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Kicked!")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Yönetici:</b> {}" \
              "\n<b>Kullanıcı:</b> {}".format(html.escape(chat.title),
                                         mention_html(user.id, user.first_name),
                                         mention_html(member.user.id, member.user.first_name))
        if reason:
            log += "\n<b>Sebep:</b> {}".format(reason)

        return log

    else:
        message.reply_text("O kullanıcıyı atamam.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Keşke yapabilseydim... ama sen bir adminsin.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Rica ederim.")
    else:
        update.effective_message.reply_text("Ha? Yapamam :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Burada olmasam kendimi nasıl kaldırırdım...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Neden zaten sohbette olan birinin yasağını kaldırmaya çalışıyorsun?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("Evet, bu kullanıcı katılabilir!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Yönetici:</b> {}" \
          "\n<b>Kullanıcı:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Sebep:</b> {}".format(reason)

    return log


@run_async
@bot_admin
def rban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Bir sohbete/kullanıcıya atıfta bulunmuyor gibisiniz.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir kullanıcıdan bahsediyor gibi görünmüyorsun.")
        return
    elif not chat_id:
        message.reply_text("Bir sohbetten bahsetmiyor gibisin.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Sohbet bulunamadı":
            message.reply_text("Sohbet bulunamadı! Geçerli bir sohbet kimliği girdiğinizden emin olun ve ben de o sohbetin parçasıyım.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("Üzgünüm ama bu özel bir sohbet!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("İnsanları orada kısıtlayamam! Yönetici olduğumdan ve kullanıcıları yasaklayabildiğimden emin olun.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Kullanıcı bulunamadı":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Keşke adminleri banlayabilseydim...")
        return

    if user_id == bot.id:
        message.reply_text("Kendimi banlamayacağım, deli misin?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Banlandı!")
    except BadRequest as excp:
        if excp.message == "Yanıt mesajı bulunamadı":
            # Do not reply
            message.reply_text('Banned!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't ban that user.")

@run_async
@bot_admin
def runban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return
    elif not chat_id:
        message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Chat not found! Make sure you entered a valid chat ID and I'm part of that chat.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("I can't unrestrict people there! Make sure I'm admin and can unban users.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user there")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
        message.reply_text("Neden o sohbette olan birinin yasağını uzaktan kaldırmaya çalışıyorsun?")
        return

    if user_id == bot.id:
        message.reply_text("I'm not gonna UNBAN myself, Ben orada bir adminim!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Yep, this user can join that chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Unbanned!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR unbanning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't unban that user.")


__help__ = """
 - /kickme: komutu veren kullanıcıyı çıkarır

*Admin only:*
 - /ban <userhandle>: kullanıcıyı yasaklar. (cevap ya da etiket).
 - /tban <userhandle> x(m/h/d): bir kullanıcıyı x süre yasaklar. (cevap ya da etiket). m = dakika, h = saat, d = gün.
 - /unban <userhandle>: yasağı kaldırır. (cevap ya da etiket).
 - /kick <userhandle>: bir kullanıcıyı çıkarır, (cevap ya da etiket).
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
