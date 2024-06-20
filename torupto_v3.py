import os
import logging
import glob
import importlib.util
import json
from telegram.ext import Application

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
def update_db(update, command_name):
    db = load_db()
    user = update.effective_user
    chat = update.effective_chat

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
            "member_count": chat.get_member_count()
        })

    # Update global command usage
    db["commands"].setdefault(command_name, 0)
    db["commands"][command_name] += 1

    save_db(db)

# Decorator for updating DB
def track_command(command_name):
    def decorator(func):
        async def wrapper(update, context):
            update_db(update, command_name)
            return await func(update, context)
        return wrapper
    return decorator

# Load modules function
def load_modules(application):
    for filename in glob.glob("./modules/*.py"):
        if filename.endswith(".py"):
            module_name = os.path.basename(filename)[:-3]
            spec = importlib.util.spec_from_file_location(module_name, filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'register'):
                module.register(application, track_command)  # Pass track_command as a keyword argument

def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("No BOT_TOKEN provided. Please set the BOT_TOKEN environment variable.")
        return

    application = Application.builder().token(token).build()

    # Load all modules dynamically
    load_modules(application)

    logger.info("Bot started successfully")
    application.run_polling()

if __name__ == '__main__':
    main()
