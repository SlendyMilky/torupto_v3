from pyrogram import filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
import logging
import requests
from PIL import Image
from io import BytesIO

# Configuration du logger pour ce module
logger = logging.getLogger('bot.image')

async def image_command(client, message: Message):
    logger.info(f"Commande /i utilisée par {message.from_user.first_name} (ID: {message.from_user.id})")
    
    # Vérifier si un lien a été fourni
    if len(message.command) < 2:
        await message.reply("Veuillez fournir un lien vers une image. Exemple : /i https://example.com/image.jpg")
        return

    image_url = message.command[1]
    
    try:
        # Télécharger l'image
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Ouvrir l'image avec Pillow
        image = Image.open(BytesIO(response.content))
        
        # Convertir l'image en PNG ou JPEG
        if image.format not in ['PNG', 'JPEG']:
            image = image.convert('RGB')
        
        # Sauvegarder l'image dans un buffer
        img_buffer = BytesIO()
        image.save(img_buffer, format='PNG' if image.mode == 'RGBA' else 'JPEG')
        img_buffer.seek(0)
        
        # Envoyer l'image
        await message.reply_photo(
            photo=img_buffer,
            caption="Voici l'image demandée en format PNG ou JPEG."
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de l'image: {str(e)}")
        await message.reply("Désolé, une erreur s'est produite lors du traitement de l'image. Veuillez vérifier le lien et réessayer.")

def register(app, track_command):
    image_handler = MessageHandler(track_command("i")(image_command), filters.command("i"))
    app.add_handler(image_handler)