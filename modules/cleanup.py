import os
import time
import logging
from apscheduler.triggers.interval import IntervalTrigger

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
                    logger.info(f"Supprimé: {filepath}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du fichier {filepath}: {e}")

        for name in dirs:
            dirpath = os.path.join(root, name)
            try:
                if os.path.getmtime(dirpath) < cutoff:
                    os.rmdir(dirpath)
                    logger.info(f"Supprimé: {dirpath}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du dossier {dirpath}: {e}")

async def scheduled_cleanup():
    """Fonction appelée périodiquement pour effectuer le nettoyage."""
    cleanup()

def register(app, track_command, scheduler):
    """Enregistre le job périodique lors du démarrage de l'application Pyrogram."""
    # Schedule the cleanup task to run every 30 minutes
    scheduler.add_job(scheduled_cleanup, IntervalTrigger(minutes=30), name="scheduled_cleanup")
