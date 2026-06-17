"""Auto-installed in traced Python processes through PYTHONPATH."""

import os
import sys

if os.environ.get("TRACESEAL_RUN_DIR"):
    try:
        from sdk.hooks import install

        install()
    except Exception as exc:  # pragma: no cover - defensive startup path
        print(f"[traceseal] failed to install hooks: {exc}", file=sys.stderr)
