from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
import logging
import subprocess

# Configure the logger for this module
logger = logging.getLogger('bot.ping')

async def ping_command(client, message: Message):
    logger.info(f"Commande /ping utilisée par {message.from_user.first_name} (ID: {message.from_user.id})")

    # Send an initial message
    initial_message = await message.reply(
        "🤡 - Pong !\n\n"
        "📶 uptobox.com : ⌛\n"
        "📶 youtube.com : ⌛\n"
        "📶 api.telegram.org : ⌛\n"
        "📶 api.alldebrid.com : ⌛",
        parse_mode=ParseMode.HTML
    )

    # Function to execute ping command and extract average time
    def execute_ping(host):
        process = subprocess.run(["ping", "-c", "5", host], capture_output=True, text=True)
        if process.returncode == 0:
            avg_time = process.stdout.split('/')[-3].split('/')[-1]  # Extract the average time
            return f"✔️ {host} : <code>{avg_time} ms</code>"
        else:
            return f"❌ {host} : Erreur"

    # Execute pings and update message
    results = {
        "uptobox.com": execute_ping("uptobox.com"),
        "youtube.com": execute_ping("youtube.com"),
        "api.telegram.org": execute_ping("api.telegram.org"),
        "api.alldebrid.com": execute_ping("api.alldebrid.com")
    }

    updated_message = (
        "🤡 - Pong !\n\n"
        f"{results['uptobox.com']}\n"
        f"{results['youtube.com']}\n"
        f"{results['api.telegram.org']}\n"
        f"{results['api.alldebrid.com']}"
    )

    await initial_message.edit_text(updated_message, parse_mode=ParseMode.HTML)

def register(app, track_command):
    ping_handler = MessageHandler(track_command("ping")(ping_command), filters.command("ping"))
    app.add_handler(ping_handler)
