from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import logging

# Configuration du logger pour ce module
logger = logging.getLogger('bot.start')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Commande /start utilisée par {update.effective_user.first_name} (ID: {update.effective_user.id})")
    message = (
        "🇨🇭 <b>Bonjour !</b>\n"
        "Je me présente, TorUpto_V3, la version améliorée du bot. "
        "Malheureusement, il n'est plus possible de télécharger des torrents et des magnets. "
        "Cependant, vous pouvez toujours télécharger des médias via des liens (vidéos, gifs et sons). "
        "Je suis ici pour vous aider à gérer ces types de fichiers ! 🤖💼\n\n"
        "🇬🇧 <b>Hello!</b>\n"
        "I am TorUpto_V3! The new version of the bot. Unfortunately, it is no longer possible to download torrents and magnets. "
        "However, you can still download media via links (videos, gifs, and sounds). "
        "I am here to help you manage these types of files! 🤖💼"
    )
    
    await update.message.reply_text(message, parse_mode="HTML")

def register(application, track_command):
    start_handler = CommandHandler("start", track_command("start")(start))
    application.add_handler(start_handler)
