"""PyInstaller entry point for the bundled TraceSeal Python Core.

The packaged binary intentionally exposes the same CLI surface as:

    python -m traceseal

Electron uses this executable only when app.isPackaged is true, so clean Windows
machines do not need a separate Python installation for dashboard-data reads.
"""

from __future__ import annotations

from traceseal.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
