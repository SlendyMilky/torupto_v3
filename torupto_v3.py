import os
import logging
import glob
from telegram.ext import Updater, CommandHandler
from telegram import ParseMode

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

# Load modules function
def load_modules(dispatcher):
    for filename in glob.glob("./modules/*.py"):
        if filename.endswith(".py"):
            module_name = os.path.basename(filename)[:-3]
            module = __import__(f'modules.{module_name}', fromlist=[module_name])
            module.register(dispatcher)

def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("No BOT_TOKEN provided. Please set the BOT_TOKEN environment variable.")
        return

    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    # Load all modules
    load_modules(dispatcher)

    logger.info("Bot started successfully")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
