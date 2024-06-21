from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
import logging

# Configuration du logger pour ce module
logger = logging.getLogger('bot.donate')

async def donate_command(client, message: Message):
    logger.info(f"Commande /donate utilisée par {message.from_user.first_name} (ID: {message.from_user.id})")
    donate_message = (
        "🇨🇭 Faites vos donations en crypto ! Choisissez parmi ces wallets :\n"
        "🇬🇧 Donate in crypto! Choose from these wallets:\n\n"
        "- Bitcoin : <code>1Cp513V36bAsQds2NMgVRLqWfzsiAmZrSs</code>\n"
        "- Ethereum : <code>0x654F5db9b9BA415e56C9070E23856426cAE607EC</code>\n"
        "- Dogecoin : <code>DMoGmrvGKsDffZxM9ePQVdz3CFPNN6utrL</code>"
    )

    await message.reply(donate_message, parse_mode=ParseMode.HTML)

def register(app, track_command):
    donate_handler = MessageHandler(track_command("donate")(donate_command), filters.command("donate"))
    app.add_handler(donate_handler)
