from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
import logging

# Configuration du logger pour ce module
logger = logging.getLogger('bot.start')

async def start_command(client, message: Message):
    logger.info(f"Commande /start utilisée par {message.from_user.first_name} (ID: {message.from_user.id})")
    start_message = (
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
    
    await message.reply(start_message, parse_mode=ParseMode.HTML)

def register(app, track_command):
    start_handler = MessageHandler(track_command("start")(start_command), filters.command("start"))
    app.add_handler(start_handler)
