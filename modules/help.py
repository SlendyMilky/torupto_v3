from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

def help_command(update: Update, context: CallbackContext):
    message = (
        "🇨🇭 <b>Aide</b>\n"
        "<i>📁 Voici comment je fonctionne : il vous suffit de m'envoyer un fichier .torrent valide ou un lien magnet valide. "
        "Ensuite, je procéderai à une recherche pour vérifier si des liens uptobox existent. Si tel est le cas, je vous enverrai chaque lien "
        "accompagné d'informations concernant le fichier. 💼🔎\n\n"
        "💡 Si le fichier n'est pas disponible sur uptobox, je m'engage à télécharger le contenu du torrent et à le téléverser. "
        "Notez que cette opération peut prendre du temps. Si le téléchargement du torrent n'est pas terminé dans les 72 heures, il sera automatiquement supprimé. 🔄⌛❌</i>\n\n"
        "🇬🇧 <b>Help</b>\n"
        "<i>📁 Here's how I operate: send me a valid .torrent file or magnet link. I'll search for uptobox links and send them to you with file info. 💼🔎\n\n"
        "💡 If the file isn't available, I'll download and upload it to uptobox. This may take time. If not completed in 72 hours, it will be deleted. 🔄⌛❌</i>"
    )
    
    update.message.reply_text(message, parse_mode=ParseMode.HTML)

def register(dispatcher):
    dispatcher.add_handler(CommandHandler("help", help_command))
