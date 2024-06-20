import os
import logging
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes, CommandHandler
import yt_dlp
from pyrogram import Client
import telegram.error  # Importation nécessaire pour gérer les exceptions de Telegram
from datetime import datetime

# Configuration pyrogram
app_id = "22197233"
app_hash = "d7d3e6143586625b7dd16d6c46655146"
token = os.getenv('BOT_TOKEN')

# Configuration du logger pour ce module
logger = logging.getLogger('bot.video_download')

# Vérifiez et créez le répertoire de téléchargement si nécessaire
download_directory = './download'
os.makedirs(download_directory, exist_ok=True)

# Une variable globale pour limiter la fréquence des mises à jour de progression
_last_progress_update_time = None

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
            context, message,
            "❌ - Aucun lien trouvé. / No link found."
        )
        return

    logger.info(f"Link verified: {link}")
    await download_video(update, context, link, message)

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE, link: str, message):
    date = '{:%Y-%m-%d}'.format(datetime.now())
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(download_directory, date + '_%(id)s.%(ext)s'),
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
            context, message,
            "📥 - Téléchargement de la vidéo... / Downloading video...",
            reset_progress=False
        )

        video_file_path = None

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            video_id = info.get("id", None)
            video_ext = info.get("ext", None)
            filename = ydl.prepare_filename(info)
            video_file_path = filename.rsplit('.', 1)[0] + '.mp4'

        await edit_or_send_message(
            context, message,
            "🔄 - Fusion des fichiers... / Merging files...",
            reset_progress=True
        )

        if os.path.getsize(video_file_path) > 2 * 1024 * 1024 * 1024:  # 2GB limit
            await edit_or_send_message(
                context, message,
                "❌ - Fichier trop grand. / File too big."
            )
            return

        await edit_or_send_message(
            context, message,
            "📤 - Téléversement de la vidéo... / Uploading video...",
            reset_progress=True
        )

        await send_video_file(context, update.effective_chat.id, video_file_path, update.message.message_id)

    except Exception as e:
        await cleanup_and_handle_error(update, context, message, e)
        return
    finally:
        if video_file_path and os.path.exists(video_file_path):
            os.remove(video_file_path)

    try:
        await context.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
    except telegram.error.BadRequest as e:
        logger.error(f"Failed to delete status message: {e}")
    except telegram.error.TimedOut as e:
        logger.error(f"Failed to delete status message due to timeout: {e}")
    except telegram.error.NetworkError as e:
        logger.error(f"Failed to delete status message due to network error: {e}")

    # Log information
    logger.info(
        f"Vidéo téléchargée par {update.effective_user.first_name} "
        f"(ID: {update.effective_user.id}, "
        f"Username: {update.effective_user.username}, "
        f"Langue: {update.effective_user.language_code})"
    )

def update_progress(status, message, context):
    if status['status'] == 'downloading':
        global _last_progress_update_time
        now = datetime.now()
        if _last_progress_update_time is None or (now - _last_progress_update_time).seconds >= 10:
            _last_progress_update_time = now
            asyncio.run_coroutine_threadsafe(
                edit_or_send_message_internal(
                    message.chat.id,
                    message.message_id,
                    "📥 - Téléchargement de la vidéo... / Downloading video...",
                    context,
                    retry_on_timeout=False
                ),
                asyncio.get_event_loop()
            )

async def send_video_file(context, chat_id, video_file_path, reply_to_message_id):
    if os.path.getsize(video_file_path) > 2 * 1024 * 1024 * 1024:
        logger.error("File too large to upload to Telegram.")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ - Fichier trop grand. / File too big.",
            parse_mode="HTML",
            reply_to_message_id=reply_to_message_id
        )
        return

    try:
        # Initialisation de Pyrogram Client
        async with Client("my_bot", api_id=app_id, api_hash=app_hash, bot_token=token) as app:
            await app.send_chat_action(chat_id, "upload_video")
            await app.send_video(
                chat_id=chat_id,
                video=video_file_path,
                reply_to_message_id=reply_to_message_id
            )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du fichier : {str(e)}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Une erreur est survenue lors de l'envoi du fichier. Veuillez réessayer plus tard.",
            parse_mode="HTML",
            reply_to_message_id=reply_to_message_id
        )

async def edit_or_send_message(context, message, new_text, reset_progress=True):
    logger.info(f"Attempting to edit message {message.message_id} to new text: {new_text}")
    if message.text == new_text:
        return  # Do not attempt to edit if the new text is the same as the current text
    await edit_or_send_message_internal(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=new_text,
        context=context,
        retry_on_timeout=True
    )

async def edit_or_send_message_internal(chat_id, message_id, text, context, retry_on_timeout=True):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode="HTML"
            )
            return
        except (telegram.error.BadRequest, telegram.error.RetryAfter, telegram.error.TimedOut, telegram.error.NetworkError) as e:
            logger.error(f"Failed to edit message (attempt {attempt+1}/{max_retries}): {e}")
            if "Message is not modified" in str(e) or "Message_id_invalid" in str(e) or "Message to edit not found" in str(e):
                logger.error(f"Message edit will not be retried due to error: {e}")
                return
            if attempt < max_retries - 1 and retry_on_timeout:
                await asyncio.sleep(5)
            else:
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=message_id
                    )
                except (telegram.error.BadRequest, telegram.error.TimedOut, telegram.error.RetryAfter, telegram.error.NetworkError) as e:
                    logger.error(f"Failed to delete message: {e}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="HTML"
                )
                return

async def cleanup_and_handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE, message, error: Exception):
    # Supprimer tous les fichiers dans le répertoire de téléchargement
    for file in os.listdir(download_directory):
        os.remove(os.path.join(download_directory, file))

    await edit_or_send_message(
        context, message,
        "❌ - Erreur. / Error."
    )
    logger.error(error)

def register(application, track_command):
    start_handler = CommandHandler("v", track_command("v")(check_link))
    application.add_handler(start_handler)
