import os
import time
import logging

# Configuration du logger pour ce module
logger = logging.getLogger('bot.cleanup')

download_directory = './download'
os.makedirs(download_directory, exist_ok=True)

def cleanup():
    """Supprime les fichiers / dossiers modifiés il y a plus de 30 minutes."""
    now = time.time()
    cutoff = now - (30 * 60)  # 30 minutes en secondes
    
    for root, dirs, files in os.walk(download_directory):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du fichier {filepath}: {e}")

        for name in dirs:
            dirpath = os.path.join(root, name)
            try:
                if os.path.getmtime(dirpath) < cutoff:
                    os.rmdir(dirpath)
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du dossier {dirpath}: {e}")

async def scheduled_cleanup(context):
    """Fonction appelée périodiquement pour effectuer le nettoyage."""
    cleanup()

def register(application, track_command=None):
    """Enregistre le job périodique lors du démarrage de l'application Telegram."""
    job_queue = application.job_queue
    job_queue.run_repeating(scheduled_cleanup, interval=30 * 60)  # Répéter toutes les 30 minutes
