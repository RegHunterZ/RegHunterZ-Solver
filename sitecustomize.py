# Auto-run; guard HiDPI policy and neutralize late calls.
try:
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtCore import Qt
    # 1) Early policy set if no instance yet
    if QGuiApplication.instance() is None:
        try:
            QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
        except Exception:
            pass

    # 2) Shim: if any module tries to set the policy AFTER the app exists,
    # silently ignore instead of raising an error.
    _orig_set = QGuiApplication.setHighDpiScaleFactorRoundingPolicy
    def _safe_set(policy):
        inst = QGuiApplication.instance()
        if inst is not None:
            # late call – ignore to avoid 'must be called before' error
            return
        try:
            return _orig_set(policy)
        except Exception:
            return
    # Rebind
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy = _safe_set  # type: ignore

except Exception:
    pass

# Export APP_LOG_LEVEL default if not set (helps early logging)
import os
os.environ.setdefault("APP_LOG_LEVEL", "DEBUG")
