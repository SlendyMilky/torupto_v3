import os
import logging
import asyncio
from pyrogram import filters, Client, enums
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
        parse_mode=enums.ParseMode.HTML
    )

    # Extraction du lien YouTube du message
    message_text = message.text
    link = message_text.split()[1] if len(message_text.split()) > 1 else None

    if not link:
        await edit_or_send_message(client, verification_message, "❌ - Aucun lien trouvé. / No link found.")
        return

    await edit_or_send_message(client, verification_message, "📥 - Téléchargement de la vidéo... / Downloading video...")
    await download_video(client, message, link, verification_message)

async def automatic_download(client: Client, message: Message):
    if message.chat.type != enums.ChatType.PRIVATE:
        return

    message_text = message.text
    if not message_text:
        return

    urls = extract_urls(message_text)
    if not urls:
        return

    for url in urls:
        await check_link_with_url(client, message, url)

async def check_link_with_url(client: Client, message: Message, link: str):
    verification_message = await message.reply(
        "🔍 - Vérification du lien... / Checking link...",
        parse_mode=enums.ParseMode.HTML
    )

    await edit_or_send_message(client, verification_message, "📥 - Téléchargement de la vidéo... / Downloading video...")
    await download_video(client, message, link, verification_message)

async def download_video(client: Client, message: Message, link: str, status_message):
    date = '{:%Y-%m-%d}'.format(datetime.now())
    
    ydl_opts_av1 = {
        'format': 'bestvideo[vcodec=av01]+bestaudio/best[vcodec=av01]/best',
        'outtmpl': os.path.join(download_directory, date + '_%(id)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'merge_output_format': 'mp4',
    }

    ydl_opts_default = {
        'format': 'bestvideo[vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(download_directory, date + '_%(id)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'merge_output_format': 'mp4',
        'addmetadata': True,
        'embedchapters': True,
        'embedsubs': True,
        'netrc': True,
        'max_filesize': 2 * 1024 * 1024 * 1024,  # 2 GB
        'recode-video': 'mp4',  # Re-encode to MP4
        'postprocessor-args': {
            'VideoConvertor': ['-c:v', 'libx264']  # Use libx264 for video encoding
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_av1) as ydl:  # Try downloading AV1 first
            info_dict = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info_dict)
            video_file_path = filename.rsplit('.', 1)[0] + '.mp4'
            logger.info(f"Video downloaded in AV1 format: {video_file_path}")
    
    except yt_dlp.DownloadError as e:
        logger.warning(f"AV1 format not available, trying default options: {e}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts_default) as ydl:  # Otherwise, use the default options
                info_dict = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info_dict)
                video_file_path = filename.rsplit('.', 1)[0] + '.mp4'
                logger.info(f"Video downloaded and processed: {video_file_path}")

        except yt_dlp.DownloadError as e:
            await cleanup_and_handle_error(client, status_message, e)
            return

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
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

def extract_urls(text):
    import re
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return url_pattern.findall(text)

def register(app, track_command):
    start_handler = MessageHandler(check_link, filters.command("v"))
    auto_download_handler = MessageHandler(automatic_download, filters.text & ~filters.create(lambda _, __, msg: msg.text and msg.text.startswith("/")))

    app.add_handler(start_handler)
    app.add_handler(auto_download_handler)

