import os
import logging
import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
import yt_dlp
from datetime import datetime

# Configuration du logger pour ce module
logger = logging.getLogger('bot.video_download')

# Vérifiez et créez le répertoire de téléchargement si nécessaire
download_directory = './download'
os.makedirs(download_directory, exist_ok=True)

async def check_link(client: Client, message: Message):
    verification_message = await message.reply(
        "🔍 - Vérification du lien... / Checking link...",
        parse_mode="HTML"
    )

    # Extraction du lien YouTube du message
    message_text = message.text
    link = message_text.split()[1] if len(message_text.split()) > 1 else None

    if not link:
        await edit_or_send_message(client, verification_message, "❌ - Aucun lien trouvé. / No link found.")
        return

    await edit_or_send_message(client, verification_message, "📥 - Téléchargement de la vidéo... / Downloading video...")
    await download_video(client, message, link, verification_message)

async def download_video(client: Client, message: Message, link: str, status_message):
    date = '{:%Y-%m-%d}'.format(datetime.now())
    ydl_opts = {
        'format': 'bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/best[vcodec^=avc1]/best[ext=mp4]/bestvideo+bestaudio/best',
        'outtmpl': os.path.join(download_directory, date + '_%(id)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'compat_opts': 'filename-sanitization',
        'addmetadata': True,
        'embedchapters': True,
        'embedsubs': True,
        'netrc': True,
        'merge_output_format': 'mp4',
        'sponsorblock_remove': ['sponsor'],
        'max_filesize': 2 * 1024 * 1024 * 1024  # 2 GB
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

            await edit_or_send_message(client, status_message, "🔄 - Traitement de la vidéo... / Processing video...")

            filename = ydl.prepare_filename(ydl.extract_info(link, download=False))
            video_file_path = filename.rsplit('.', 1)[0] + '.mp4'
    except yt_dlp.DownloadError as e:
        await cleanup_and_handle_error(client, status_message, e)
        return

    if os.path.getsize(video_file_path) > 2 * 1024 * 1024 * 1024:
        os.remove(video_file_path)
        await edit_or_send_message(client, status_message, "❌ - Fichier trop grand. / File too big.")
        return

    await edit_or_send_message(client, status_message, "📤 - Téléversement de la vidéo... / Uploading video...")

    await client.send_video(
        chat_id=message.chat.id,
        video=video_file_path,
        reply_to_message_id=message.id
    )

    os.remove(video_file_path)

    await client.delete_messages(
        chat_id=message.chat.id,
        message_ids=status_message.id
    )

    # Logging information
    logger.info(
        f"Vidéo téléchargée par {message.from_user.first_name} (ID: {message.from_user.id}, "
        f"Username: {message.from_user.username}, Langue: {message.from_user.language_code})"
    )

async def edit_or_send_message(client, status_message, new_text):
    try:
        await client.edit_message_text(
            chat_id=status_message.chat.id,
            message_id=status_message.id,
            text=new_text,
            parse_mode="HTML"
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
            parse_mode="HTML"
        )

async def cleanup_and_handle_error(client, status_message, error: Exception):
    # Supprimer tous les fichiers dans le répertoire de téléchargement
    for f in os.listdir(download_directory):
        os.remove(os.path.join(download_directory, f))

    await edit_or_send_message(client, status_message, "❌ - Erreur lors du téléchargement. / Error during download.")
    logger.error(error)

def register(app, track_command):
    start_handler = MessageHandler(check_link, filters.command("v"))
    app.add_handler(start_handler)
