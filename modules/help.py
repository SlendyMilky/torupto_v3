from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import logging

# Configuration du logger pour ce module
logger = logging.getLogger('bot.help')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Commande /help utilisée par {update.effective_user.first_name} (ID: {update.effective_user.id})")
    message = (
        "🇨🇭 <b>Aide</b>\n"
        "<i>📁 Voici comment je fonctionne : malheureusement, il n'est plus possible de télécharger des torrents et des magnets. "
        "Cependant, vous pouvez m'envoyer un lien de média (vidéo, gif ou son) et je vous aiderai à gérer ce type de fichier. "
        "Je vous fournirai des informations détaillées dès que vous m'enverrez le lien. 💼🔎\n\n"
        "💡 Pour toute question ou assistance supplémentaire, n'hésitez pas à me contacter. 📩</i>\n\n"
        "🇬🇧 <b>Help</b>\n"
        "<i>📁 Here's how I operate: unfortunately, it is no longer possible to download torrents and magnets. "
        "However, you can send me a media link (video, gif, or sound) and I will help you manage this type of file. "
        "I will provide detailed information as soon as you send me the link. 💼🔎\n\n"
        "💡 For any further questions or assistance, feel free to contact me. 📩</i>"
    )

    await update.message.reply_text(message, parse_mode="HTML")

def register(application, track_command):
    help_handler = CommandHandler("help", track_command("help")(help_command))
    application.add_handler(help_handler)
