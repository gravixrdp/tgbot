import asyncio
from typing import Optional

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButtonRequestChat,
    KeyboardButtonRequestUsers,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


def main_menu():
    # Buttons to request share of Group, Channel, User, and Bot
    group_btn = KeyboardButton(
        text="✅ Group",
        request_chat=KeyboardButtonRequestChat(
            request_id=101,
            chat_is_channel=False,   # groups/supergroups
        ),
    )
    channel_btn = KeyboardButton(
        text="📣 Channel",
        request_chat=KeyboardButtonRequestChat(
            request_id=102,
            chat_is_channel=True,  # channels
        ),
    )
    user_btn = KeyboardButton(
        text="👤 User",
        request_users=KeyboardButtonRequestUsers(
            request_id=201,
            user_is_bot=False,
        ),
    )
    bot_btn = KeyboardButton(
        text="🤖 Bot",
        request_users=KeyboardButtonRequestUsers(
            request_id=202,
            user_is_bot=True,
        ),
    )

    return ReplyKeyboardMarkup(
        [
            [group_btn, channel_btn],
            [user_btn, bot_btn],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else "Unknown"
    text = (
        "👋 Welcome to ID Bot!\n\n"
        "Use this bot to get the User, Bot, Group, or Channel ID in any of these ways:\n"
        "✅ Forward a message\n"
        "✅ Share a chat using the buttons\n"
        "✅ Share a contact\n"
        "✅ Reply from another chat\n\n"
        f"Your Id: <code>{user_id}</code>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_menu())


def render_id_line(title: str, _id: Optional[int]) -> str:
    if _id is None:
        return ""
    return f"{title}: <code>{_id}</code>\n"


async def handle_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Central handler to pick IDs from whatever the user sends:
    - Forwarded messages
    - Reply messages
    - Contacts
    - Shared users/chats via keyboard buttons
    - Normal messages (show sender/user/chat IDs)
    """
    m = update.effective_message
    pieces = []

    # 1) Basic info about the sender and current chat
    if m:
        if m.from_user:
            pieces.append(render_id_line("From User Id", m.from_user.id))
        if m.sender_chat:
            # When the message is posted as a channel or anonymous admin
            pieces.append(render_id_line("Sender Chat Id", m.sender_chat.id))
        if m.chat:
            pieces.append(render_id_line("This Chat Id", m.chat.id))

    # 2) Forwarded content
    if m and (m.forward_from or m.forward_from_chat):
        if m.forward_from:
            pieces.append(render_id_line("Forwarded From User Id", m.forward_from.id))
        if m.forward_from_chat:
            pieces.append(render_id_line("Forwarded From Chat/Channel Id", m.forward_from_chat.id))

    # 3) Reply context (if replying to a message from another chat/user)
    if m and m.reply_to_message:
        rm = m.reply_to_message
        if rm.from_user:
            pieces.append(render_id_line("Replied Msg From User Id", rm.from_user.id))
        if rm.sender_chat:
            pieces.append(render_id_line("Replied Msg Sender Chat Id", rm.sender_chat.id))
        if rm.chat:
            pieces.append(render_id_line("Replied Msg Chat Id", rm.chat.id))

    # 4) Shared contact
    if m and m.contact:
        pieces.append(render_id_line("Contact User Id", m.contact.user_id))

    # 5) New Bot API share objects
    users_shared = getattr(m, "users_shared", None)
    if users_shared and getattr(users_shared, "users", None):
        for idx, u in enumerate(users_shared.users, start=1):
            pieces.append(render_id_line(f"Shared User {idx} Id", u.user_id))

    chat_shared = getattr(m, "chat_shared", None)
    if chat_shared:
        pieces.append(render_id_line("Shared Chat Id", chat_shared.chat_id))

    # If nothing detected, guide the user
    if not pieces:
        await m.reply_text(
            "Send or forward a message, share a chat using the buttons, share a contact, or reply to a message.\n"
            "I'll extract the ID for you.",
            reply_markup=main_menu(),
        )
        return

    # Reply with collected IDs
    text = "Here are the IDs I found:\n" + "".join(pieces)
    await m.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=main_menu())


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_everything))

    return app


if __name__ == "__main__":
    # Bot token set as requested by user (left unchanged)
    BOT_TOKEN = "8413258612:AAFzX_I3VGeObBymm_vTNINDOeZJE2XELXQ"
    app = build_app(BOT_TOKEN)
    # run_polling is a blocking helper that manages the event loop internally
    app.run_polling(allowed_updates=Update.ALL_TYPES)