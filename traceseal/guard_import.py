from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from traceseal.guard_schema import (
    SCHEMA_VERSION,
    GuardEventError,
    load_guard_events,
    validate_guard_event,
    validate_guard_health_event,
    validate_guard_process_spawn_event,
)

GUARD_ARTIFACT_NAME = "guard_events.jsonl"
GUARD_MANIFEST_KEY = "guard"


class GuardImportError(ValueError):
    """Raised when Guard events cannot be safely attached to a run."""


def _require_run_dir(run_dir: str | Path) -> Path:
    path = Path(run_dir).resolve()
    if not path.exists():
        raise GuardImportError(f"run directory does not exist: {path}")
    if not path.is_dir():
        raise GuardImportError(f"run path is not a directory: {path}")
    return path


def _read_manifest(run_dir: Path, *, strict: bool) -> dict[str, Any]:
    path = run_dir / "manifest.json"
    if not path.exists():
        return {"run_id": run_dir.name}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        if strict:
            raise GuardImportError(f"cannot read run manifest {path}: {error}") from error
        return {}
    if not isinstance(value, dict):
        if strict:
            raise GuardImportError(f"run manifest must contain a JSON object: {path}")
        return {}
    return value


def _safe_artifact_path(run_dir: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        return None
    candidate = (run_dir / value).resolve()
    try:
        candidate.relative_to(run_dir.resolve())
    except ValueError:
        return None
    return candidate


def maybe_find_guard_events(run_dir: str | Path) -> Path | None:
    """Return the optional imported Guard artifact without requiring metadata."""

    path = Path(run_dir).resolve()
    if not path.is_dir():
        return None

    manifest = _read_manifest(path, strict=False)
    guard = manifest.get(GUARD_MANIFEST_KEY)
    if isinstance(guard, Mapping):
        candidate = _safe_artifact_path(path, guard.get("guard_events_path"))
        if candidate is not None and candidate.is_file():
            return candidate

    canonical = (path / GUARD_ARTIFACT_NAME).resolve()
    try:
        canonical.relative_to(path)
    except ValueError:
        return None
    return canonical if canonical.is_file() else None


def _validate_import_events(
    events: list[dict[str, Any]], *, run_id: str
) -> list[dict[str, Any]]:
    if not events:
        raise GuardImportError("Guard JSONL artifact contains no events")

    validated: list[dict[str, Any]] = []
    event_ids: set[str] = set()
    for index, event in enumerate(events, start=1):
        event_type = event.get("event_type")
        try:
            if event_type == "guard.health":
                validate_guard_health_event(event)
            elif event_type == "process.spawn":
                validate_guard_process_spawn_event(event)
            else:
                # guard.event.v1 explicitly permits forward-compatible unknown types.
                validate_guard_event(event)
        except GuardEventError as error:
            raise GuardImportError(f"Guard event {index} failed validation: {error}") from error

        event_run_id = event.get("run_id")
        if event_run_id is not None and event_run_id != run_id:
            raise GuardImportError(
                f"Guard event {index} run_id {event_run_id!r} does not match {run_id!r}"
            )

        event_id = str(event["event_id"])
        if event_id in event_ids:
            raise GuardImportError(f"duplicate Guard event_id: {event_id}")
        event_ids.add(event_id)
        validated.append(event)
    return validated


def _load_and_validate(path: Path, *, run_id: str) -> list[dict[str, Any]]:
    try:
        events = load_guard_events(path)
    except GuardEventError as error:
        raise GuardImportError(f"cannot parse Guard artifact {path}: {error}") from error
    return _validate_import_events(events, run_id=run_id)


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _serialized_jsonl(events: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(event, ensure_ascii=False, separators=(",", ":"), default=str)
        + "\n"
        for event in events
    )


def _summary(
    events: list[dict[str, Any]],
    *,
    path: str | None,
    imported_at: str | None,
) -> dict[str, Any]:
    return {
        "guard_events_path": path,
        "guard_event_count": len(events),
        "guard_event_types": sorted({str(event["event_type"]) for event in events}),
        "guard_schema_version": SCHEMA_VERSION if events else None,
        "guard_imported_at": imported_at,
    }


def import_guard_events(
    run_dir: str | Path, guard_jsonl_path: str | Path
) -> dict[str, Any]:
    """Validate and attach a Guard JSONL artifact without merging timeline events."""

    run_path = _require_run_dir(run_dir)
    source = Path(guard_jsonl_path).resolve()
    if not source.exists():
        raise GuardImportError(f"Guard JSONL artifact does not exist: {source}")
    if not source.is_file():
        raise GuardImportError(f"Guard JSONL path is not a file: {source}")

    manifest = _read_manifest(run_path, strict=True)
    run_id = str(manifest.get("run_id") or run_path.name)
    events = _load_and_validate(source, run_id=run_id)
    destination = (run_path / GUARD_ARTIFACT_NAME).resolve()
    same_artifact = source == destination
    if destination.exists() and not same_artifact:
        raise GuardImportError(
            f"imported Guard artifact already exists: {destination}; refusing to overwrite"
        )

    imported_at = datetime.now(timezone.utc).isoformat()
    metadata = _summary(
        events,
        path=GUARD_ARTIFACT_NAME,
        imported_at=imported_at,
    )

    if not same_artifact:
        _write_atomic(destination, _serialized_jsonl(events))
    manifest[GUARD_MANIFEST_KEY] = metadata
    _write_atomic(
        run_path / "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n",
    )
    return metadata


def load_imported_guard_events(run_dir: str | Path) -> list[dict[str, Any]]:
    """Load and validate an optional imported Guard artifact."""

    run_path = _require_run_dir(run_dir)
    artifact = maybe_find_guard_events(run_path)
    if artifact is None:
        return []
    manifest = _read_manifest(run_path, strict=False)
    run_id = str(manifest.get("run_id") or run_path.name)
    return _load_and_validate(artifact, run_id=run_id)


def get_guard_event_summary(run_dir: str | Path) -> dict[str, Any]:
    """Return a validated optional Guard summary without dashboard integration."""

    run_path = _require_run_dir(run_dir)
    artifact = maybe_find_guard_events(run_path)
    manifest = _read_manifest(run_path, strict=False)
    guard = manifest.get(GUARD_MANIFEST_KEY)
    imported_at = guard.get("guard_imported_at") if isinstance(guard, Mapping) else None
    if artifact is None:
        return _summary([], path=None, imported_at=None)
    events = load_imported_guard_events(run_path)
    return _summary(
        events,
        path=GUARD_ARTIFACT_NAME,
        imported_at=imported_at if isinstance(imported_at, str) else None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m traceseal.guard_import",
        description="Validate and attach Guard JSONL events to an existing TraceSeal run",
    )
    parser.add_argument("--run", required=True, help="existing TraceSeal run directory")
    parser.add_argument(
        "--guard-events", required=True, help="source guard.event.v1 JSONL artifact"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = import_guard_events(args.run, args.guard_events)
    except GuardImportError as error:
        print(f"guard import failed: {error}", file=sys.stderr)
        return 2
    print(
        "imported "
        f"{result['guard_event_count']} Guard event(s); "
        f"types={result['guard_event_types']} artifact={result['guard_events_path']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
