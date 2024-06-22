from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
import logging
import asyncio
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

    hosts = ["uptobox.com", "youtube.com", "api.telegram.org", "api.alldebrid.com"]
    results = {}

    # Execute pings one after another and update message
    for host in hosts:
        results[host] = execute_ping(host)
        updated_message = (
            "🤡 - Pong !\n\n"
            f"{results.get('uptobox.com', '📶 uptobox.com : ⌛')}\n"
            f"{results.get('youtube.com', '📶 youtube.com : ⌛')}\n"
            f"{results.get('api.telegram.org', '📶 api.telegram.org : ⌛')}\n"
            f"{results.get('api.alldebrid.com', '📶 api.alldebrid.com : ⌛')}"
        )
        await initial_message.edit_text(updated_message, parse_mode=ParseMode.HTML)
        await asyncio.sleep(1)  # Adding a small delay for better user experience

def register(app, track_command):
    ping_handler = MessageHandler(track_command("ping")(ping_command), filters.command("ping"))
    app.add_handler(ping_handler)
