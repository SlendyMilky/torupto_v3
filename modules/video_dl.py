import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application
import yt_dlp
import telegram.error  # Importation nécessaire pour gérer les exceptions de Telegram

# Configuration du logger pour ce module
logger = logging.getLogger('bot.video_download')

# Vérifiez et créez le répertoire de téléchargement si nécessaire
download_directory = './download'
os.makedirs(download_directory, exist_ok=True)

# Progression globale
progress_stages = {
    'Checking link': 0.0,
    'Downloading': 0.3,
    'Merging': 0.6,
    'Uploading': 0.9,
    'Done': 1.0
}

def progress_bar(progress):
    bar_length = 20
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    return f"[{bar}] {int(100 * progress)}%"

async def check_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🔍 - Vérification du lien... / Checking link...\n{progress_bar(progress_stages['Checking link'])}",
        parse_mode="HTML",
        reply_to_message_id=update.message.message_id
    )

    # Extraction du lien YouTube du message
    message_text = update.message.text
    link = message_text.split()[1] if len(message_text.split()) > 1 else None

    if not link:
        await edit_or_send_message(
            update, context, message,
            f"❌ - Aucun lien trouvé. / No link found.\n{progress_bar(progress_stages['Done'])}"
        )
        return

    await download_video(update, context, link, message)

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE, link: str, message):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(download_directory, '%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'progress_hooks': [lambda d: update_progress(d, message, context)],
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'merge_output_format': 'mp4',
    }

    try:
        await edit_or_send_message(
            update, context, message,
            f"📥 - Téléchargement de la vidéo... / Downloading video...\n{progress_bar(progress_stages['Downloading'])}",
            reset_progress=False
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            video_file_path = filename.rsplit('.', 1)[0] + '.mp4'

        await edit_or_send_message(
            update, context, message,
            f"🔄 - Fusion des fichiers... / Merging files...\n{progress_bar(progress_stages['Merging'])}",
            reset_progress=False
        )

        if os.path.getsize(video_file_path) > 2 * 1024 * 1024 * 1024:
            os.remove(video_file_path)
            await edit_or_send_message(
                update, context, message,
                f"❌ - Fichier trop grand. / File too big.\n{progress_bar(progress_stages['Done'])}"
            )
            return

        await edit_or_send_message(
            update, context, message,
            f"📤 - Téléversement de la vidéo... / Uploading video...\n{progress_bar(progress_stages['Uploading'])}",
            reset_progress=False
        )

        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=open(video_file_path, 'rb'),
            reply_to_message_id=update.message.message_id
        )

    except Exception as e:
        await cleanup_and_handle_error(update, context, message, e)
        return

    os.remove(video_file_path)

    # Suppression du message de statut après l'envoi de la vidéo
    try:
        await context.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
    except telegram.error.BadRequest as e:
        logger.error(f"Failed to delete status message: {e}")

    # Logging information
    logger.info(
        f"Vidéo téléchargée par {update.effective_user.first_name} "
        f"(ID: {update.effective_user.id}, "
        f"Username: {update.effective_user.username}, "
        f"Langue: {update.effective_user.language_code})"
    )

def update_progress(status, message, context):
    if status['status'] == 'downloading':
        total = status.get('total_bytes_estimate') or status.get('total_bytes') or 1
        progress = status.get('downloaded_bytes', 0)
        partial_progress = progress / total * 0.3 + progress_stages['Downloading'] 

        progress_message = f"📥 - Téléchargement de la vidéo... / Downloading video...\n{progress_bar(partial_progress)}"
        asyncio.run_coroutine_threadsafe(
            context.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=progress_message,
                parse_mode="HTML"
            ),
            asyncio.get_event_loop()
        )

async def edit_or_send_message(update, context, message, new_text, reset_progress=True):
    try:
        await context.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=new_text,
            parse_mode="HTML"
        )
    except (telegram.error.BadRequest, telegram.error.TimedOut, telegram.error.RetryAfter) as e:
        logger.error(f"Failed to edit message: {e}")
        try:
            await context.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id
            )
        except (telegram.error.BadRequest, telegram.error.TimedOut, telegram.error.RetryAfter) as e:
            logger.error(f"Failed to delete message: {e}")
        if reset_progress:
            text = new_text if new_text else ""
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=new_text,
            parse_mode="HTML",
            reply_to_message_id=update.message.message_id
        )

async def cleanup_and_handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE, message, error: Exception):
    # Supprimer tous les fichiers dans le répertoire de téléchargement
    for file in os.listdir(download_directory):
        os.remove(os.path.join(download_directory, file))

    await edit_or_send_message(
        update, context, message,
        f"❌ - Erreur lors du téléchargement. / Error during download.\n{progress_bar(progress_stages['Done'])}"
    )
    logger.error(error)

def register(application, track_command):
    start_handler = CommandHandler("v", track_command("v")(check_link))
    application.add_handler(start_handler)
