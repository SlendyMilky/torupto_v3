from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
import logging

# Configuration du logger pour ce module
logger = logging.getLogger('bot.help')

async def help_command(client, message: Message):
    logger.info(f"Commande /help utilisée par {message.from_user.first_name} (ID: {message.from_user.id})")
    help_message = (
        "🇨🇭 <b>Aide</b>\n"
        "<i>📁 Voici comment je fonctionne : malheureusement, il n'est plus possible de télécharger des torrents et des magnets. "
        "Cependant, vous pouvez m'envoyer un lien de média (vidéo, gif ou son) et je vous aiderai à gérer ce type de fichier. "
        "Je vous fournirai des informations détaillées dès que vous m'enverrez le lien. 💼🔎\n\n"
        "🇬🇧 <b>Help</b>\n"
        "<i>📁 Here's how I operate: unfortunately, it is no longer possible to download torrents and magnets. "
        "However, you can send me a media link (video, gif, or sound) and I will help you manage this type of file. "
        "I will provide detailed information as soon as you send me the link. 💼🔎\n\n"
    )

    await message.reply(help_message, parse_mode=ParseMode.HTML)

def register(app, track_command):
    help_handler = MessageHandler(track_command("help")(help_command), filters.command("help"))
    app.add_handler(help_handler)
