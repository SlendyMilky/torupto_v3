import os
import logging
import glob
import importlib.util
import json
import inspect
from pyrogram import Client, filters
from pyrogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Configuration du logger
logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s [%(name)s] %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

file_handler = logging.FileHandler("bot_log.txt")
file_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# File path for JSON DB
DB_FILE_PATH = "./database/bot_db.json"

# Load and save DB functions
def load_db():
    if os.path.exists(DB_FILE_PATH):
        with open(DB_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {"users": {}, "groups": {}, "commands": {}}

def save_db(db):
    os.makedirs(os.path.dirname(DB_FILE_PATH), exist_ok=True)
    with open(DB_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

# Update DB function
def update_db(update: Message, command_name):
    db = load_db()
    user = update.from_user
    chat = update.chat

    user_info = db["users"].setdefault(str(user.id), {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "command_count": {}
    })

    user_info["command_count"].setdefault(command_name, 0)
    user_info["command_count"][command_name] += 1

    if chat.type in ["group", "supergroup"]:
        group_info = db["groups"].setdefault(str(chat.id), {
            "title": chat.title,
            "member_count": chat.members_count
        })

    # Update global command usage
    db["commands"].setdefault(command_name, 0)
    db["commands"][command_name] += 1

    save_db(db)

# Decorator for updating DB
def track_command(command_name):
    def decorator(func):
        async def wrapper(client, message):
            update_db(message, command_name)
            return await func(client, message)
        return wrapper
    return decorator

# Load modules function
def load_modules(app, scheduler):
    for filename in glob.glob("./modules/*.py"):
        if filename.endswith(".py"):
            module_name = os.path.basename(filename)[:-3]
            spec = importlib.util.spec_from_file_location(module_name, filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'register'):
                # Check if the register function has a parameter for the scheduler
                register_spec = inspect.getfullargspec(module.register)
                if 'scheduler' in register_spec.args:
                    module.register(app, track_command, scheduler)  # Pass track_command and scheduler
                else:
                    module.register(app, track_command)  # Pass only track_command

def main():
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    bot_token = os.getenv('BOT_TOKEN')

    if not api_id or not api_hash or not bot_token:
        logger.error("Missing API_ID, API_HASH or BOT_TOKEN. Please set the corresponding environment variables.")
        return

    app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
    scheduler = AsyncIOScheduler()

    # Load all modules dynamically
    load_modules(app, scheduler)

    @app.on_message(filters.command("start"))
    @track_command("start")
    async def start_command(client, message):
        await message.reply("Bot started successfully")

    logger.info("Bot started successfully")
    scheduler.start()
    app.run()

if __name__ == '__main__':
    main()
