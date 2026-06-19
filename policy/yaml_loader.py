from __future__ import annotations

import json
import os
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from .dsl import validate_policy


def workspace_root(workspace: str | Path | None = None) -> Path:
    if workspace is not None:
        return Path(workspace).resolve()
    configured = os.environ.get("TRACESEAL_WORKSPACE_ROOT")
    return Path(configured).resolve() if configured else Path.cwd().resolve()


def _default_policy() -> tuple[dict[str, Any], str | None]:
    resource = resources.files("policy").joinpath("default_policy.json")
    try:
        return json.loads(resource.read_text(encoding="utf-8")), str(resource)
    except Exception:
        from .rules import DEFAULT_RULES

        return DEFAULT_RULES, None


def load_policy_with_source(workspace: str | Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    root = workspace_root(workspace)
    selected = next((path for path in (root / "policy.yaml", root / "policy.yml") if path.is_file()), None)
    if selected is None:
        policy, default_path = _default_policy()
        return policy, {"type": "json_default", "path": default_path, "error": None}
    try:
        raw = yaml.safe_load(selected.read_text(encoding="utf-8"))
        return validate_policy(raw), {"type": "yaml", "path": str(selected), "error": None}
    except Exception as exc:
        policy, _ = _default_policy()
        return policy, {
            "type": "yaml_error_fallback",
            "path": str(selected),
            "error": f"{type(exc).__name__}: {exc}",
        }
