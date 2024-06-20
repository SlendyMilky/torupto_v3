from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

def donate_command(update: Update, context: CallbackContext):
    message = (
        "🇨🇭 Faites vos donations en crypto ! Choisissez parmi ces wallets :\n"
        "🇬🇧 Donate in crypto! Choose from these wallets:\n\n"
        "- Bitcoin : <code>1Cp513V36bAsQds2NMgVRLqWfzsiAmZrSs</code>\n"
        "- Ethereum : <code>0x654F5db9b9BA415e56C9070E23856426cAE607EC</code>\n"
        "- Dogecoin : <code>DMoGmrvGKsDffZxM9ePQVdz3CFPNN6utrL</code>"
    )

    update.message.reply_text(message, parse_mode=ParseMode.HTML)

def register(dispatcher):
    dispatcher.add_handler(CommandHandler("donate", donate_command))
