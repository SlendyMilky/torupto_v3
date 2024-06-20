from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import logging

# Configuration du logger pour ce module
logger = logging.getLogger('bot.donate')

async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Commande /donate utilisée par {update.effective_user.first_name} (ID: {update.effective_user.id})")
    message = (
        "🇨🇭 Faites vos donations en crypto ! Choisissez parmi ces wallets :\n"
        "🇬🇧 Donate in crypto! Choose from these wallets:\n\n"
        "- Bitcoin : <code>1Cp513V36bAsQds2NMgVRLqWfzsiAmZrSs</code>\n"
        "- Ethereum : <code>0x654F5db9b9BA415e56C9070E23856426cAE607EC</code>\n"
        "- Dogecoin : <code>DMoGmrvGKsDffZxM9ePQVdz3CFPNN6utrL</code>"
    )

    await update.message.reply_text(message, parse_mode="HTML")

def register(application, track_command):
    donate_handler = CommandHandler("donate", track_command("donate")(donate_command))
    application.add_handler(donate_handler)
