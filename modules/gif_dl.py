import os
import logging
import asyncio
from pyrogram import filters, Client, enums
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
import yt_dlp
from datetime import datetime

# Configuration du logger pour ce module
logger = logging.getLogger('bot.gif_download')

# Vérifiez et créez le répertoire de téléchargement si nécessaire
download_directory = './download'
os.makedirs(download_directory, exist_ok=True)

async def check_gif_link(client: Client, message: Message):
    verification_message = await message.reply(
        "🔍 - Vérification du lien... / Checking link...",
        parse_mode=enums.ParseMode.HTML
    )

    # Extraction du lien GIF du message
    message_text = message.text
    link = message_text.split()[1] if len(message_text.split()) > 1 else None

    if not link:
        await edit_or_send_message(client, verification_message, "❌ - Aucun lien trouvé. / No link found.")
        return

    await edit_or_send_message(client, verification_message, "📥 - Téléchargement du GIF... / Downloading GIF...")
    await download_gif(client, message, link, verification_message)

async def download_gif(client: Client, message: Message, link: str, status_message):
    date = '{:%Y-%m-%d}'.format(datetime.now())

    ydl_opts = {
        'format': 'best[ext=gif]/best',
        'outtmpl': os.path.join(download_directory, date + '_%(id)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'merge_output_format': 'gif',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info_dict)
            gif_file_path = filename.rsplit('.', 1)[0] + '.gif'
            logger.info(f"GIF downloaded: {gif_file_path}")

    except yt_dlp.DownloadError as e:
        await cleanup_and_handle_error(client, status_message, e)
        return

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await cleanup_and_handle_error(client, status_message, e)
        return

    await edit_or_send_message(client, status_message, "📤 - Téléversement du GIF... / Uploading GIF...")

    await client.send_document(
        chat_id=message.chat.id,
        document=gif_file_path,
        reply_to_message_id=message.id
    )

    os.remove(gif_file_path)

    await client.delete_messages(
        chat_id=message.chat.id,
        message_ids=status_message.id
    )

    # Logging information
    logger.info(
        f"GIF téléchargé par {message.from_user.first_name} (ID: {message.from_user.id}, "
        f"Username: {message.from_user.username}, Langue: {message.from_user.language_code})"
    )

async def edit_or_send_message(client, status_message, new_text):
    try:
        await client.edit_message_text(
            chat_id=status_message.chat.id,
            message_id=status_message.id,
            text=new_text,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        logger.error(e)
        await client.delete_messages(
            chat_id=status_message.chat.id,
            message_ids=status_message.id
        )
        return await client.send_message(
            chat_id=status_message.chat.id,
            text=new_text,
            parse_mode=enums.ParseMode.HTML
        )

async def cleanup_and_handle_error(client, status_message, error: Exception):
    # Supprimer tous les fichiers dans le répertoire de téléchargement
    for f in os.listdir(download_directory):
        os.remove(os.path.join(download_directory, f))

    await edit_or_send_message(client, status_message, "❌ - Erreur lors du téléchargement. / Error during download.")
    logger.error(error)

def register(app, track_command):
    start_handler = MessageHandler(track_command("g")(check_gif_link), filters.command("g"))
    app.add_handler(start_handler)
