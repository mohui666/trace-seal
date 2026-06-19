from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import httpx


def main() -> None:
    # The demo installs the checked-in example inside its disposable TraceSeal
    # sandbox. No real credentials, remote Git operation, or external host is used.
    shutil.copyfile(Path("examples/policy.yaml"), Path("policy.yaml"))
    Path(".env.demo").write_text("DEMO_TOKEN=demo-value-not-a-secret\n", encoding="utf-8")

    target = Path("demo-delete-target")
    target.mkdir(exist_ok=True)
    (target / "sample.txt").write_text("demo\n", encoding="utf-8")
    delete_result = subprocess.run(["rm", "-rf", str(target)], check=False)
    print(f"dangerous delete return code: {delete_result.returncode}")

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True}, request=request)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        response = client.post(
            "http://127.0.0.1/demo?token=demo-value-not-a-secret",
            headers={"Authorization": "Bearer demo-value-not-a-secret"},
            json={"message": "offline demo"},
        )
    print(f"local HTTP status: {response.status_code}")


if __name__ == "__main__":
    main()
