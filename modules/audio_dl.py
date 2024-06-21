from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message
from pyrogram.enums import ParseMode
import yt_dlp
import logging
import os
import asyncio

# Configuration du logger pour ce module
logger = logging.getLogger('bot.audio_download')

download_directory = './download'
os.makedirs(download_directory, exist_ok=True)

async def check_link(client, message: Message):
    verification_message = await message.reply(
        "🔍 - Vérification du lien... / Checking link...",
        parse_mode=ParseMode.HTML
    )

    # Extraction du lien YouTube du message
    message_text = message.text
    link = message_text.split()[1] if len(message_text.split()) > 1 else None

    if not link:
        await edit_or_send_message(client, verification_message, "❌ - Aucun lien trouvé. / No link found.")
        return

    await edit_or_send_message(client, verification_message, "📥 - Téléchargement de l'audio... / Downloading audio...")
    await download_audio(client, message, link, verification_message)

async def download_audio(client, message, link: str, status_message):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_directory, '%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'progress_hooks': [],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }, {
            'key': 'EmbedThumbnail',
        }, {
            'key': 'FFmpegMetadata',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

            await edit_or_send_message(client, status_message, "🔄 - Traitement de l'audio... / Processing audio...")

            filename = ydl.prepare_filename(ydl.extract_info(link, download=False))
            audio_file_path = filename.rsplit('.', 1)[0] + '.mp3'
    except yt_dlp.DownloadError as e:
        await cleanup_and_handle_error(client, status_message, e)
        return

    if os.path.getsize(audio_file_path) > 2 * 1024 * 1024 * 1024:
        os.remove(audio_file_path)
        await edit_or_send_message(client, status_message, "❌ - Fichier trop grand. / File too big.")
        return

    await edit_or_send_message(client, status_message, "📤 - Téléversement de l'audio... / Uploading audio...")

    await client.send_audio(
        chat_id=message.chat.id,
        audio=audio_file_path,
        reply_to_message_id=message.id
    )

    os.remove(audio_file_path)

    await client.delete_messages(
        chat_id=message.chat.id,
        message_ids=status_message.id
    )

    # Logging information
    logger.info(
        f"Audio téléchargé par {message.from_user.first_name} (ID: {message.from_user.id}, "
        f"Username: {message.from_user.username}, Langue: {message.from_user.language_code})"
    )

async def edit_or_send_message(client, status_message, new_text):
    try:
        await client.edit_message_text(
            chat_id=status_message.chat.id,
            message_id=status_message.id,
            text=new_text,
            parse_mode=ParseMode.HTML
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
            parse_mode=ParseMode.HTML
        )

async def cleanup_and_handle_error(client, status_message, error: Exception):
    # Supprimer tous les fichiers dans le répertoire de téléchargement
    for f in os.listdir(download_directory):
        os.remove(os.path.join(download_directory, f))

    await edit_or_send_message(client, status_message, "❌ - Erreur lors du téléchargement. / Error during download.")
    logger.error(error)

def register(app, track_command):
    start_handler = MessageHandler(track_command("a")(check_link), filters.command("a"))
    app.add_handler(start_handler)
