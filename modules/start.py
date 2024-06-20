from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

def start(update: Update, context: CallbackContext):
    message = (
        "🇨🇭 <b>Bonjour !</b>\n"
        "Je me présente, TorUpto_V3, la version améliorée du bot. "
        "Mon objectif est de vous fournir un lien uptobox pour tout fichier torrent ou magnet que vous m'envoyez. "
        "En cas d'indisponibilité d'un torrent/magnet, je m'engage à le télécharger et à le téléverser sur https://uptobox.com ! 🤖💼\n\n"
        "🇬🇧 <b>Hello!</b>\n"
        "I am TorUpto_V3! The new version of the bot. My goal is to send you an uptobox link for any torrent or magnet file you send me. "
        "If a torrent/magnet is not available, I will ensure to download it and then upload it to https://uptobox.com! 🤖💼"
    )
    
    update.message.reply_text(message, parse_mode=ParseMode.HTML)

def register(dispatcher):
    dispatcher.add_handler(CommandHandler("start", start))
