from __future__ import annotations

import builtins
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

from policy.rules import command_to_string, evaluate_file_write, evaluate_http_request, evaluate_shell_command, is_git_push, is_rm_rf, rm_targets
from recorder.core import record_event, summarize_env
from recorder.workspace import diff_trees, snapshot_tree

_INSTALLED = False
_SUPPRESS_FILE_EVENTS = 0

_ORIG_OPEN = builtins.open
_ORIG_SUBPROCESS_RUN = subprocess.run
_ORIG_OS_SYSTEM = os.system
_ORIG_PATH_WRITE_TEXT = Path.write_text
_ORIG_PATH_WRITE_BYTES = Path.write_bytes
_ORIG_SHUTIL_RMTREE = shutil.rmtree
_ORIG_OS_REMOVE = os.remove
_ORIG_OS_UNLINK = os.unlink
_ORIG_URLLIB_URLOPEN = urllib.request.urlopen

try:  # requests is optional in the MVP.
    import requests  # type: ignore

    _ORIG_REQUESTS_SESSION_REQUEST = requests.sessions.Session.request
except Exception:  # pragma: no cover - optional dependency
    requests = None  # type: ignore
    _ORIG_REQUESTS_SESSION_REQUEST = None


def _workspace_root() -> Path:
    return Path(os.environ.get("TRACESEAL_WORKSPACE_ROOT", os.getcwd())).resolve()


def _run_dir() -> Path | None:
    value = os.environ.get("TRACESEAL_RUN_DIR")
    return Path(value).resolve() if value else None


def _rel_path(path: Any) -> str:
    root = _workspace_root()
    try:
        p = Path(path)
        return p.resolve().relative_to(root).as_posix() if p.is_absolute() else p.as_posix()
    except Exception:
        return str(path)


def _offline_http_enabled() -> bool:
    return os.environ.get("TRACESEAL_OFFLINE_HTTP", "").lower() in {"1", "true", "yes", "on"}


def _is_trace_internal(path: Any) -> bool:
    run_dir = _run_dir()
    if run_dir is None or path is None:
        return False
    try:
        p = Path(path).resolve()
        # The sandbox workspace lives under runs/<id>/workspace. We must record
        # writes there; only TraceSeal metadata files directly under run_dir are
        # internal recorder state.
        try:
            p.relative_to(_workspace_root())
            return False
        except ValueError:
            pass
        p.relative_to(run_dir)
        return True
    except Exception:
        return False


def _command_tokens(args: Any) -> list[str] | None:
    if isinstance(args, (list, tuple)):
        return [str(x) for x in args]
    return None


def _decode_output(value: Any, limit: int = 4000) -> Any:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value[:limit].decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value[:limit]
    return str(value)[:limit]


def _record_file_event(operation: str, path: Any, before: dict[str, Any], after: dict[str, Any], extra_output: dict[str, Any] | None = None) -> None:
    if _SUPPRESS_FILE_EVENTS:
        return
    if path is None or _is_trace_internal(path):
        return
    root = _workspace_root()
    changes = diff_trees(before, after)
    if not changes and operation in {"file.write", "file.delete"}:
        return
    rel = _rel_path(path)
    risk = (
        evaluate_file_write(rel)
        if operation == "file.write"
        else {"level": "medium", "reasons": [f"deleted path: {rel}"], "policy_rule": "file_delete", "action": "warn"}
    )
    record_event(
        {
            "type": operation,
            "operation": operation,
            "input": {"path": rel},
            "output": {"status": "ok", **(extra_output or {})},
            "risk": risk,
            "file_changes": changes,
        }
    )


class _TracingFile:
    def __init__(self, wrapped: Any, path: Any, mode: str, before: dict[str, Any]):
        self._wrapped = wrapped
        self._path = path
        self._mode = mode
        self._before = before
        self._closed_recorded = False
        self._bytes_written = 0

    def write(self, data: Any) -> Any:
        result = self._wrapped.write(data)
        try:
            if isinstance(data, (bytes, bytearray)):
                self._bytes_written += len(data)
            else:
                self._bytes_written += len(str(data).encode("utf-8", errors="replace"))
        except Exception:
            pass
        return result

    def writelines(self, lines: Any) -> Any:
        cached = list(lines)
        result = self._wrapped.writelines(cached)
        for line in cached:
            try:
                self._bytes_written += len(line if isinstance(line, (bytes, bytearray)) else str(line).encode("utf-8", errors="replace"))
            except Exception:
                pass
        return result

    def close(self) -> Any:
        try:
            return self._wrapped.close()
        finally:
            self._record_close()

    def _record_close(self) -> None:
        if self._closed_recorded:
            return
        self._closed_recorded = True
        try:
            after = snapshot_tree(self._path, _workspace_root())
            _record_file_event("file.write", self._path, self._before, after, {"bytes_written": self._bytes_written, "mode": self._mode})
        except Exception:
            pass

    def __enter__(self) -> "_TracingFile":
        self._wrapped.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Any:
        try:
            return self._wrapped.__exit__(exc_type, exc, tb)
        finally:
            self._record_close()

    def __iter__(self):
        return iter(self._wrapped)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)


def _is_write_mode(mode: Any) -> bool:
    return any(flag in str(mode or "r") for flag in ["w", "a", "x", "+"])


def traced_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
    if not _is_write_mode(mode) or _is_trace_internal(file):
        return _ORIG_OPEN(file, mode, *args, **kwargs)
    rel = _rel_path(file)
    risk = evaluate_file_write(rel)
    if risk.get("action") == "deny":
        record_event(
            {
                "type": "file.write",
                "operation": "open",
                "input": {"path": rel, "mode": mode},
                "output": {"status": "blocked", "exception": "TraceSeal policy denied file write"},
                "risk": risk,
                "file_changes": [],
            }
        )
        raise PermissionError(f"TraceSeal policy denied file write: {rel}")
    before = snapshot_tree(file, _workspace_root())
    wrapped = _ORIG_OPEN(file, mode, *args, **kwargs)
    return _TracingFile(wrapped, file, mode, before)


def traced_path_write_text(self: Path, data: str, *args: Any, **kwargs: Any) -> int:
    rel = _rel_path(self)
    risk = evaluate_file_write(rel)
    if risk.get("action") == "deny":
        record_event(
            {
                "type": "file.write",
                "operation": "Path.write_text",
                "input": {"path": rel},
                "output": {"status": "blocked", "exception": "TraceSeal policy denied file write", "api": "Path.write_text"},
                "risk": risk,
                "file_changes": [],
            }
        )
        raise PermissionError(f"TraceSeal policy denied file write: {rel}")
    before = snapshot_tree(self, _workspace_root())
    result = _ORIG_PATH_WRITE_TEXT(self, data, *args, **kwargs)
    after = snapshot_tree(self, _workspace_root())
    encoding = kwargs.get("encoding") or "utf-8"
    _record_file_event("file.write", self, before, after, {"bytes_written": len(data.encode(encoding, errors="replace")), "api": "Path.write_text"})
    return result


def traced_path_write_bytes(self: Path, data: bytes, *args: Any, **kwargs: Any) -> int:
    rel = _rel_path(self)
    risk = evaluate_file_write(rel)
    if risk.get("action") == "deny":
        record_event(
            {
                "type": "file.write",
                "operation": "Path.write_bytes",
                "input": {"path": rel},
                "output": {"status": "blocked", "exception": "TraceSeal policy denied file write", "api": "Path.write_bytes"},
                "risk": risk,
                "file_changes": [],
            }
        )
        raise PermissionError(f"TraceSeal policy denied file write: {rel}")
    before = snapshot_tree(self, _workspace_root())
    result = _ORIG_PATH_WRITE_BYTES(self, data, *args, **kwargs)
    after = snapshot_tree(self, _workspace_root())
    _record_file_event("file.write", self, before, after, {"bytes_written": len(data), "api": "Path.write_bytes"})
    return result


def _delete_path(path: str | os.PathLike[str]) -> None:
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    if p.is_dir() and not p.is_symlink():
        _ORIG_SHUTIL_RMTREE(p)
    elif p.exists() or p.is_symlink():
        _ORIG_OS_UNLINK(p)


def _simulate_rm_rf(args: Any, command: str, tokens: list[str] | None, check: bool, start: float) -> subprocess.CompletedProcess:
    global _SUPPRESS_FILE_EVENTS
    targets = rm_targets(command, tokens) or []
    root = _workspace_root()
    before: dict[str, dict[str, Any]] = {}
    for target in targets:
        before.update(snapshot_tree(target, root))

    risk = evaluate_shell_command(command, tokens)
    blocked = risk.get("action") == "deny"
    returncode = 126 if blocked else 0
    stderr = "TraceSeal policy denied dangerous delete" if blocked else None

    if not blocked:
        _SUPPRESS_FILE_EVENTS += 1
        try:
            for target in targets:
                try:
                    _delete_path(target)
                except FileNotFoundError:
                    pass
        finally:
            _SUPPRESS_FILE_EVENTS -= 1

    after: dict[str, dict[str, Any]] = {}
    for target in targets:
        after.update(snapshot_tree(target, root))
    changes = diff_trees(before, after)

    record_event(
        {
            "type": "shell",
            "operation": "subprocess.run",
            "duration_ms": int((time.time() - start) * 1000),
            "input": {"command": command, "args": tokens, "targets": targets, "shell": False, "simulated": True},
            "output": {
                "status": "blocked" if blocked else "ok",
                "returncode": returncode,
                "stderr": stderr,
                "simulation": "python shutil/os delete for cross-platform rm -rf MVP",
            },
            "risk": risk,
            "file_changes": changes,
        }
    )
    completed = subprocess.CompletedProcess(args=args, returncode=returncode, stdout=None, stderr=stderr)
    if check and returncode != 0:
        raise subprocess.CalledProcessError(returncode, args, output=None, stderr=stderr)
    return completed


def _simulate_git_push(args: Any, command: str, tokens: list[str] | None, shell: bool, check: bool, start: float) -> subprocess.CompletedProcess:
    """Record git push without contacting any remote."""

    risk = evaluate_shell_command(command, tokens)
    blocked = risk.get("action") == "deny"
    returncode = 126 if blocked else 0
    stderr = "TraceSeal policy denied git push" if blocked else None
    stdout = None if blocked else "TraceSeal simulated git push; no remote contacted"
    record_event(
        {
            "type": "shell",
            "operation": "subprocess.run",
            "duration_ms": int((time.time() - start) * 1000),
            "input": {"command": command, "args": tokens, "shell": shell, "simulated": True},
            "output": {
                "status": "blocked" if blocked else "simulated",
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "simulation": "git push is not executed in TraceSeal MVP demos",
            },
            "risk": risk,
            "file_changes": [],
        }
    )
    completed = subprocess.CompletedProcess(args=args, returncode=returncode, stdout=stdout, stderr=stderr)
    if check and returncode != 0:
        raise subprocess.CalledProcessError(returncode, args, output=stdout, stderr=stderr)
    return completed


def traced_subprocess_run(*popenargs: Any, **kwargs: Any) -> subprocess.CompletedProcess:
    args = popenargs[0] if popenargs else kwargs.get("args")
    shell = bool(kwargs.get("shell", False))
    command = command_to_string(args, shell)
    tokens = _command_tokens(args)
    risk = evaluate_shell_command(command, tokens)
    check = bool(kwargs.pop("check", False))
    start = time.time()

    if is_rm_rf(command, tokens):
        return _simulate_rm_rf(args, command, tokens, check, start)

    if is_git_push(command, tokens):
        return _simulate_git_push(args, command, tokens, shell, check, start)

    if risk.get("action") == "deny":
        returncode = 126
        stderr = "TraceSeal policy denied shell command"
        record_event(
            {
                "type": "shell",
                "operation": "subprocess.run",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"command": command, "args": tokens, "shell": shell},
                "output": {"status": "blocked", "returncode": returncode, "stderr": stderr},
                "risk": risk,
                "file_changes": [],
            }
        )
        if check:
            raise subprocess.CalledProcessError(returncode, args, output=None, stderr=stderr)
        return subprocess.CompletedProcess(args=args, returncode=returncode, stdout=None, stderr=stderr)

    try:
        completed = _ORIG_SUBPROCESS_RUN(*popenargs, check=False, **kwargs)
        record_event(
            {
                "type": "shell",
                "operation": "subprocess.run",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"command": command, "args": tokens, "shell": shell},
                "output": {
                    "status": "ok" if completed.returncode == 0 else "failed",
                    "returncode": completed.returncode,
                    "stdout": _decode_output(getattr(completed, "stdout", None)),
                    "stderr": _decode_output(getattr(completed, "stderr", None)),
                },
                "risk": risk,
                "file_changes": [],
            }
        )
        if check and completed.returncode != 0:
            raise subprocess.CalledProcessError(completed.returncode, args, output=getattr(completed, "stdout", None), stderr=getattr(completed, "stderr", None))
        return completed
    except Exception as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            raise
        record_event(
            {
                "type": "shell",
                "operation": "subprocess.run",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"command": command, "args": tokens, "shell": shell},
                "output": {"status": "exception", "exception": repr(exc)},
                "risk": risk,
                "file_changes": [],
            }
        )
        raise


def _os_system_exit_code(status: int) -> int:
    """Return the shell exit code while preserving os.system's raw result."""

    if os.name == "nt":
        return status
    try:
        return os.waitstatus_to_exitcode(status)
    except (AttributeError, ValueError):  # pragma: no cover - legacy/platform fallback
        return status


def _os_system_blocked_status() -> int:
    # os.system returns a wait status on POSIX and the shell return code on
    # Windows. Use the conventional "command cannot execute" exit code.
    return 126 if os.name == "nt" else 126 << 8


def traced_os_system(command: str) -> int:
    """Trace and apply shell policy to an os.system command."""

    command_text = str(command)
    tokens = None  # Let the shared policy tokenize raw shell syntax itself.
    risk = evaluate_shell_command(command_text, tokens)
    start = time.time()

    targets = rm_targets(command_text, tokens) if is_rm_rf(command_text, tokens) else []
    before: dict[str, dict[str, Any]] = {}
    for target in targets:
        before.update(snapshot_tree(target, _workspace_root()))

    if risk.get("action") == "deny":
        status = _os_system_blocked_status()
        record_event(
            {
                "type": "shell",
                "operation": "os.system",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"command": command_text, "args": None, "targets": targets, "shell": True},
                "output": {
                    "status": "blocked",
                    "returncode": status,
                    "exit_code": _os_system_exit_code(status),
                    "stderr": "TraceSeal policy denied os.system command",
                },
                "risk": risk,
                "file_changes": [],
            }
        )
        return status

    try:
        status = _ORIG_OS_SYSTEM(command_text)
        after: dict[str, dict[str, Any]] = {}
        for target in targets:
            after.update(snapshot_tree(target, _workspace_root()))
        exit_code = _os_system_exit_code(status)
        record_event(
            {
                "type": "shell",
                "operation": "os.system",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"command": command_text, "args": None, "targets": targets, "shell": True},
                "output": {
                    "status": "ok" if exit_code == 0 else "failed",
                    "returncode": status,
                    "exit_code": exit_code,
                },
                "risk": risk,
                "file_changes": diff_trees(before, after),
            }
        )
        return status
    except Exception as exc:
        record_event(
            {
                "type": "shell",
                "operation": "os.system",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"command": command_text, "args": None, "targets": targets, "shell": True},
                "output": {"status": "exception", "exception": repr(exc)},
                "risk": risk,
                "file_changes": [],
            }
        )
        raise


def traced_rmtree(path: Any, *args: Any, **kwargs: Any) -> Any:
    before = snapshot_tree(path, _workspace_root())
    try:
        return _ORIG_SHUTIL_RMTREE(path, *args, **kwargs)
    finally:
        after = snapshot_tree(path, _workspace_root())
        _record_file_event("file.delete", path, before, after)


def traced_remove(path: Any, *args: Any, **kwargs: Any) -> Any:
    before = snapshot_tree(path, _workspace_root())
    try:
        return _ORIG_OS_REMOVE(path, *args, **kwargs)
    finally:
        after = snapshot_tree(path, _workspace_root())
        _record_file_event("file.delete", path, before, after)


def traced_unlink(path: Any, *args: Any, **kwargs: Any) -> Any:
    before = snapshot_tree(path, _workspace_root())
    try:
        return _ORIG_OS_UNLINK(path, *args, **kwargs)
    finally:
        after = snapshot_tree(path, _workspace_root())
        _record_file_event("file.delete", path, before, after)


class _OfflineHTTPResponse:
    """Tiny urllib-like response used by examples/tests to avoid real network."""

    status = 0
    code = 0

    def __init__(self, url: str):
        self.url = url

    def read(self, *_args: Any, **_kwargs: Any) -> bytes:
        return b""

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> "_OfflineHTTPResponse":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None


def traced_urlopen(url: Any, *args: Any, **kwargs: Any) -> Any:
    method = "GET"
    display_url = getattr(url, "full_url", url)
    if hasattr(url, "get_method"):
        try:
            method = url.get_method()
        except Exception:
            method = "GET"
    start = time.time()
    risk = evaluate_http_request(method, str(display_url))
    if risk.get("action") == "deny":
        record_event(
            {
                "type": "http",
                "operation": "urllib.request.urlopen",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"method": method, "url": str(display_url)},
                "output": {"status": "blocked", "exception": "TraceSeal policy denied HTTP request"},
                "risk": risk,
                "file_changes": [],
            }
        )
        raise PermissionError(f"TraceSeal policy denied HTTP request: {method} {display_url}")
    if _offline_http_enabled():
        response = _OfflineHTTPResponse(str(display_url))
        record_event(
            {
                "type": "http",
                "operation": "urllib.request.urlopen",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"method": method, "url": str(display_url), "offline_simulated": True},
                "output": {"status": "simulated", "code": response.status},
                "risk": risk,
                "file_changes": [],
            }
        )
        return response
    try:
        response = _ORIG_URLLIB_URLOPEN(url, *args, **kwargs)
        record_event(
            {
                "type": "http",
                "operation": "urllib.request.urlopen",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"method": method, "url": str(display_url)},
                "output": {"status": "ok", "code": getattr(response, "status", None)},
                "risk": risk,
                "file_changes": [],
            }
        )
        return response
    except Exception as exc:
        record_event(
            {
                "type": "http",
                "operation": "urllib.request.urlopen",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"method": method, "url": str(display_url)},
                "output": {"status": "exception", "exception": repr(exc)},
                "risk": risk,
                "file_changes": [],
            }
        )
        raise


def traced_requests_request(self: Any, method: str, url: str, **kwargs: Any) -> Any:
    start = time.time()
    risk = evaluate_http_request(method, url)
    if risk.get("action") == "deny":
        record_event(
            {
                "type": "http",
                "operation": "requests.Session.request",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"method": method, "url": url},
                "output": {"status": "blocked", "exception": "TraceSeal policy denied HTTP request"},
                "risk": risk,
                "file_changes": [],
            }
        )
        raise PermissionError(f"TraceSeal policy denied HTTP request: {method} {url}")
    if _offline_http_enabled():
        response = requests.Response()  # type: ignore[union-attr]
        response.status_code = 0
        response.url = url
        response._content = b""
        record_event(
            {
                "type": "http",
                "operation": "requests.Session.request",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"method": method, "url": url, "offline_simulated": True},
                "output": {"status": "simulated", "status_code": 0},
                "risk": risk,
                "file_changes": [],
            }
        )
        return response
    try:
        response = _ORIG_REQUESTS_SESSION_REQUEST(self, method, url, **kwargs)  # type: ignore[misc]
        record_event(
            {
                "type": "http",
                "operation": "requests.Session.request",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"method": method, "url": url},
                "output": {"status": "ok", "status_code": getattr(response, "status_code", None)},
                "risk": risk,
                "file_changes": [],
            }
        )
        return response
    except Exception as exc:
        record_event(
            {
                "type": "http",
                "operation": "requests.Session.request",
                "duration_ms": int((time.time() - start) * 1000),
                "input": {"method": method, "url": url},
                "output": {"status": "exception", "exception": repr(exc)},
                "risk": risk,
                "file_changes": [],
            }
        )
        raise


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    builtins.open = traced_open
    subprocess.run = traced_subprocess_run
    os.system = traced_os_system
    Path.write_text = traced_path_write_text
    Path.write_bytes = traced_path_write_bytes
    shutil.rmtree = traced_rmtree
    os.remove = traced_remove
    os.unlink = traced_unlink
    urllib.request.urlopen = traced_urlopen
    if requests is not None and _ORIG_REQUESTS_SESSION_REQUEST is not None:  # pragma: no branch
        requests.sessions.Session.request = traced_requests_request
    record_event(
        {
            "type": "sdk",
            "operation": "install_hooks",
            "input": {"pid": os.getpid()},
            "output": {"status": "ok", "hooks": ["open", "Path.write_text", "subprocess.run", "os.system", "urllib", "requests?", "shutil.rmtree", "os.remove"]},
            "risk": {"level": "low", "reasons": [], "policy_rule": None, "action": "allow"},
            "file_changes": [],
            "env": summarize_env(),
        }
    )
