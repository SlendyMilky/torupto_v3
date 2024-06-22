from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
import logging
import requests
import os
from datetime import datetime

# Configure the logger for this module
logger = logging.getLogger('bot.api_info')

# Get the necessary environment variables
OWNER_USER_ID = int(os.getenv("OWNER_USER_ID"))
ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")
ALLDEBRID_AGENT = 'toruptov2'
ALLDEBRID_URL = f"https://api.alldebrid.com/v4/user?agent={ALLDEBRID_AGENT}&apikey={ALLDEBRID_API_KEY}"

async def api_info_command(client, message: Message):
    logger.info(f"Commande /api_info utilisée par {message.from_user.first_name} (ID: {message.from_user.id})")
    
    if message.from_user.id != OWNER_USER_ID:
        await message.reply(
            "<b>🇨🇭 Refusé</b>\nVous n'êtes pas autorisé à faire cette commande. ❌ \nEn cas de problème contactez le créateur via la commande /contact. 📧\n\n"
            "<b>🇬🇧 Denied</b>\nYou are not authorized to execute this command. ❌\nIn case of any issues, please contact the owner with /contact. 📧",
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.id
        )
        return

    # Make the API request to Alldebrid
    response = requests.get(ALLDEBRID_URL)
    if response.status_code == 200:
        data = response.json()
        user_info = data['data']['user']
        premium_until_timestamp = user_info['premiumUntil']
        
        # Convert timestamp to datetime object
        premium_until_datetime = datetime.fromtimestamp(premium_until_timestamp)
        formatted_premium_until = premium_until_datetime.strftime('%d-%m-%Y')
        
        # Construct the message text
        info_text = (
            f"👤 Username : <b>{user_info['username']}</b>\n"
            f"🔖 Premium : <b>{user_info['isPremium']}</b>\n"
            f"⏳ Premium until : <b>{formatted_premium_until}</b>\n"
            f"🎯 Fidelity Point : <b>{user_info['fidelityPoints']}</b>"
        )
        await message.reply(info_text, parse_mode=ParseMode.HTML, reply_to_message_id=message.id)
    else:
        await message.reply("Failed to retrieve API information.", reply_to_message_id=message.id)

def register(app, track_command):
    api_info_handler = MessageHandler(track_command("api_info")(api_info_command), filters.command("api_info"))
    app.add_handler(api_info_handler)
