import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOG_DIR = Path.home() / ".biopygeon" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

logger = logging.getLogger("biopygeon")
logger.setLevel(logging.ERROR)

handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=2)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
