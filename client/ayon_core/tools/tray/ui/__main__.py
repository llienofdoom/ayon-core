from __future__ import annotations

try:
    from . import tray
except ImportError:
    import tray


tray.main()
