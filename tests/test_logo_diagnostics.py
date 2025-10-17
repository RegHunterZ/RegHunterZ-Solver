
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from ai_coach.diag.logo_check import run_logo_diagnostics

def test_logo_diag_structure():
    r = run_logo_diagnostics()
    assert "candidates" in r and isinstance(r["candidates"], list)
    assert len(r["candidates"]) >= 1
    # keys present
    for k in ("python","platform","cwd","qt_image_formats","pixmap_is_null"):
        assert k in r
