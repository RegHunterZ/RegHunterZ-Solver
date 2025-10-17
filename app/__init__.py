# Clean bootstrap for KKPoker Solver app package

# Ensure HiDPI policy BEFORE any QApplication exists
from .hidpi import ensure_policy_before_qapp
ensure_policy_before_qapp()

# Logging bootstrap
import sys, logging
from .logger import setup as _log_setup
_logger, _logfile = _log_setup()

def _log_excepthook(exc_type, exc, tb):
    try:
        logging.getLogger('unhandled').error('UNHANDLED', exc_info=(exc_type, exc, tb))
    except Exception:
        pass
sys.excepthook = _log_excepthook

# Tesseract autodetect as early as possible
try:
    from .tesseract_finder import ensure_pytesseract_cmd
    _tcmd = ensure_pytesseract_cmd()
except Exception:
    _tcmd = None
