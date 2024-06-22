from pyrogram import Client, filters
from pyrogram.types import (Message, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, CallbackQuery)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.enums import ParseMode
import os
from datetime import datetime
import logging

# Configure le logger pour ce module
logger = logging.getLogger('bot.contact')

# Récupère les variables d'environnement nécessaires
OWNER_USER_ID = int(os.getenv("OWNER_USER_ID"))
CONTACT_CHAT_ID = int(os.getenv("CONTACT_CHAT_ID"))

# Stockage temporaire pour les IDs de message de demande
request_message_ids = {}

async def contact_command(client, message: Message):
    logger.info(f"Commande /contact utilisée par {message.from_user.first_name} (ID: {message.from_user.id})")
    
    request_message = await message.reply(
        "<b>🇨🇭 Dite moi le message à transmettre au propriétaire du bot.</b>\n\n"
        "<b>🇬🇧 Tell me the message to send to the bot owner.</b>",
        reply_markup=ForceReply(),
        parse_mode=ParseMode.HTML
    )

    # Stocke l'ID du message de demande pour filtrer les réponses
    request_message_ids[message.chat.id] = request_message.id

async def reply_callback(client, message: Message):
    request_message_id = request_message_ids.get(message.chat.id)
    if request_message_id and message.reply_to_message and message.reply_to_message.id == request_message_id:
        contact_info = (
            f"<b>📞 - Demande de contact !</b>\n"
            f"<b>ℹ️ - Telegram</b>\n"
            f"👤 User : @{message.from_user.username}\n"
            f"🆔 ID : <code>{message.from_user.id}</code>\n"
            f"🤖 Bot : {message.from_user.is_bot}\n"
            f"👤 Name : {message.from_user.first_name} {message.from_user.last_name}\n"
            f"💬 Chat : <code>{message.chat.id}</code>\n"
            f"🌐 Langue : {message.from_user.language_code}\n\n"
            f"<b>ℹ️ - Message</b>\n"
            f"{message.text}\n\n"
            f"📅 Date : {datetime.now().strftime('%d.%m.%Y / %H:%M:%S')}"
        )
        
        await client.send_message(
            chat_id=CONTACT_CHAT_ID,
            text=contact_info,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Répondre au message", callback_data=f"/reponse,cid:{message.chat.id},mid:{message.id}")]]
            )
        )
        await message.reply("✅ - Le message a bien été transféré. / The message has been transferred.")
        
        # Efface l'ID du message de demande stocké
        del request_message_ids[message.chat.id]

async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    if data and data.startswith("/reponse"):
        cid = data.split("cid:")[1].split(",")[0]
        mid = data.split("mid:")[1]
        
        await client.send_message(
            chat_id=callback_query.message.chat.id,
            text=f"🧪 - Réponse à envoyer à [{cid}] pour le message [{mid}]",
            reply_markup=ForceReply(),
            parse_mode=ParseMode.HTML
        )
        
        # Répond à la callback_query pour empêcher Telegram d'attendre
        await callback_query.answer("Réponse initiée. / Response initiated.", show_alert=False)

async def handle_forced_reply(client: Client, message: Message):
    if message.reply_to_message and message.reply_to_message.text.startswith("🧪 - Réponse à envoyer à"):
        # Extraire les informations d'ID de chat et d'ID de message
        parts = message.reply_to_message.text.split(" ")
        cid = parts[5].strip("[]")
        mid = parts[9].strip("[]")

        await client.send_message(
            chat_id=int(cid),
            text=(
                f"<b>🔔 - Message du propriétaire ! / Message from the owner !</b>\n\n"
                f"💬 - <code>{message.text}</code>\n\n"
                f"⚠️ - 🇨🇭 Mon propriétaire ne pourra pas voir votre réponse, veuillez utiliser la commande de contact pour cela.\n"
                f"⚠️ - 🇬🇧 My owner will not be able to see your reply, please use the contact command for that."
            ),
            parse_mode=ParseMode.HTML,
            reply_to_message_id=int(mid)  # S'assure que nous répondons au message spécifique
        )
        await message.reply("✅ - La réponse a bien été envoyée. / The reply has been sent.")

  
def register(app, track_command):
    contact_handler = MessageHandler(track_command("contact")(contact_command), filters.command("contact"))
    reply_handler = MessageHandler(reply_callback, filters.reply & filters.text)
    callback_query_handler = CallbackQueryHandler(handle_callback_query, filters.regex(r"^/reponse"))
    forced_reply_handler = MessageHandler(handle_forced_reply, filters.reply & filters.text)

    app.add_handler(contact_handler)
    app.add_handler(reply_handler)
    app.add_handler(callback_query_handler)
    app.add_handler(forced_reply_handler)
