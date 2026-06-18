"""Safe demo for TraceSeal Python-level file read tracking.

The files contain only synthetic demo values and live inside the sandbox.
Their contents are never printed or stored in TraceSeal events.
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    demo = Path("trace_file_read_demo")
    secret_dir = demo / "secrets"
    unicode_dir = demo / "Unicode 路径 with spaces"
    secret_dir.mkdir(parents=True, exist_ok=True)
    unicode_dir.mkdir(parents=True, exist_ok=True)

    normal = demo / "notes.txt"
    binary = unicode_dir / "payload.bin"
    sensitive = secret_dir / "demo.env"
    normal.write_text("ordinary demo notes\n", encoding="utf-8")
    binary.write_bytes(b"\x00TraceSeal-demo\xff")
    sensitive.write_text("DEMO_TOKEN=not-a-real-secret\n", encoding="utf-8")

    with open(normal, "r", encoding="utf-8") as handle:
        normal_length = len(handle.read())
    with open(binary, "rb") as handle:
        binary_length = len(handle.read())
    with normal.open("r", encoding="utf-8") as handle:
        path_open_length = len(handle.readline())
    sensitive_length = len(sensitive.read_text(encoding="utf-8"))
    path_bytes_length = len(binary.read_bytes())

    try:
        open(demo / "missing.txt", "r", encoding="utf-8")
    except FileNotFoundError:
        print("missing file read failed as expected")

    print(
        "read metadata lengths:",
        normal_length,
        binary_length,
        path_open_length,
        sensitive_length,
        path_bytes_length,
    )


if __name__ == "__main__":
    main()
