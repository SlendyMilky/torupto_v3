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
            "📥 - Téléchargement de la vidéo... / Downloading video...",
            reset_progress=False
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            video_file_path = filename.rsplit('.', 1)[0] + '.mp4'

        await edit_or_send_message(
            update, context, message,
            "🔄 - Fusion des fichiers... / Merging files...",
            reset_progress=False
        )

        if os.path.getsize(video_file_path) > 2 * 1024 * 1024 * 1024:
            os.remove(video_file_path)
            await edit_or_send_message(
                update, context, message,
                "❌ - Fichier trop grand. / File too big."
            )
            return

        await edit_or_send_message(
            update, context, message,
            "📤 - Téléversement de la vidéo... / Uploading video...",
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
    except telegram.error.TimedOut as e:
        logger.error(f"Failed to delete status message due to timeout: {e}")
    except telegram.error.NetworkError as e:
        logger.error(f"Failed to delete status message due to network error: {e}")

    # Logging information
    logger.info(
        f"Vidéo téléchargée par {update.effective_user.first_name} "
        f"(ID: {update.effective_user.id}, "
        f"Username: {update.effective_user.username}, "
        f"Langue: {update.effective_user.language_code})"
    )

def update_progress(status, message, context):
    if status['status'] == 'downloading':
        # Seuil pour éditer le message toutes les 10% de progression
        if status.get('elapsed', 0) % 10 == 0:
            progress_message = "📥 - Téléchargement de la vidéo... / Downloading video..."
            asyncio.run_coroutine_threadsafe(
                edit_or_send_message_internal(
                    message.chat.id,
                    message.message_id,
                    progress_message,
                    context,
                    retry_on_timeout=False
                ),
                asyncio.get_event_loop()
            )

async def edit_or_send_message(update, context, message, new_text, reset_progress=True):
    await edit_or_send_message_internal(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=new_text,
        context=context,
        retry_on_timeout=True
    )

async def edit_or_send_message_internal(chat_id, message_id, text, context, retry_on_timeout=True):
    max_retries = 3  # Réduction du nombre maximal de tentatives
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
            if attempt < max_retries - 1 and retry_on_timeout:
                await asyncio.sleep(5)  # Attendre un peu plus longtemps
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
        update, context, message,
        "❌ - Erreur lors du téléchargement. / Error during download."
    )
    logger.error(error)

def register(application, track_command):
    start_handler = CommandHandler("v", track_command("v")(check_link))
    application.add_handler(start_handler)

if __name__ == "__main__":
    # Configuration du bot et lancement de votre application
    app = Application.builder().token("YOUR_BOT_TOKEN_HERE").build()
    register(app, lambda x: x)
    app.run_polling()
