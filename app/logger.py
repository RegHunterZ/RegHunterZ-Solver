import logging, os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

def setup(level_str: str | None = None):
    level = getattr(logging, (level_str or os.getenv("APP_LOG_LEVEL") or "DEBUG").upper(), logging.DEBUG)
    logger = logging.getLogger()
    if logger.handlers:
        # Avoid double setup
        return logger
    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(level)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(level)
    logger.addHandler(ch)

    logging.getLogger(__name__).info("Logger initialized. Level=%s, file=%s", logging.getLevelName(level), LOG_FILE)
    return logger, LOG_FILE
