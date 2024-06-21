from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp
import logging
import os
import asyncio

# Configuration du logger pour ce module
logger = logging.getLogger('bot.audio_download')

download_directory = './download'
os.makedirs(download_directory, exist_ok=True)

def progress_bar(progress, total):
    bar_length = 20
    filled_length = int(bar_length * progress // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    return f"[{bar}] {int(100 * progress / total)}%"

async def check_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🔍 - Vérification du lien... / Checking link...",
        parse_mode="HTML",
        reply_to_message_id=update.message.message_id
    )

    # Extraction du lien YouTube du message
    message_text = update.message.text
    link = message_text.split()[1] if len(message_text.split()) > 1 else None

    if not link:
        await edit_or_send_message(
            update, context, message,
            "❌ - Aucun lien trouvé. / No link found."
        )
        return

    await download_audio(update, context, link, message)

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, link: str, message):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_directory, '%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'progress_hooks': [lambda d: update_progress(d, message, context)],
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
            filename = ydl.prepare_filename(ydl.extract_info(link, download=False))
            audio_file_path = filename.rsplit('.', 1)[0] + '.mp3'
    except yt_dlp.DownloadError as e:
        await cleanup_and_handle_error(update, context, message, e)
        return

    if os.path.getsize(audio_file_path) > 2 * 1024 * 1024 * 1024:
        os.remove(audio_file_path)
        await edit_or_send_message(
            update, context, message,
            "❌ - Fichier trop grand. / File too big."
        )
        return

    await edit_or_send_message(
        update, context, message,
        "📤 - Téléversement de l'audio... / Uploading audio..."
    )

    await context.bot.send_audio(
        chat_id=update.effective_chat.id,
        audio=open(audio_file_path, 'rb'),
        reply_to_message_id=update.message.message_id
    )

    os.remove(audio_file_path)

    # Suppression du message de statut après l'envoi de l'audio
    await context.bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.message_id
    )

    # Logging information
    logger.info(
        f"Audio téléchargé par {update.effective_user.first_name} "
        f"(ID: {update.effective_user.id}, "
        f"Username: {update.effective_user.username}, "
        f"Langue: {update.effective_user.language_code})"
    )

def update_progress(status, message, context):
    if status['status'] == 'downloading':
        total = status.get('total_bytes_estimate') or status.get('total_bytes') or 1
        progress = status.get('downloaded_bytes', 0)
        progress_message = f"📥 - Téléchargement de l'audio... / Downloading audio...\n{progress_bar(progress, total)}"
        asyncio.run_coroutine_threadsafe(
            context.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=progress_message,
                parse_mode="HTML"
            ),
            asyncio.get_event_loop()
        )

async def edit_or_send_message(update, context, message, new_text):
    try:
        await context.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=new_text,
            parse_mode="HTML"
        )
    except:
        await context.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
        return await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=new_text,
            parse_mode="HTML",
            reply_to_message_id=update.message.message_id
        )

async def cleanup_and_handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE, message, error: Exception):
    # Supprimer tous les fichiers dans le répertoire de téléchargement
    for f in os.listdir(download_directory):
        os.remove(os.path.join(download_directory, f))

    await edit_or_send_message(
        update, context, message,
        "❌ - Erreur lors du téléchargement. / Error during download."
    )
    logger.error(error)

def register(application, track_command):
    start_handler = CommandHandler("a", track_command("a")(check_link))
    application.add_handler(start_handler)
