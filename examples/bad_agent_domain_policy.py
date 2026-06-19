"""Exercise domain policy decisions entirely through httpx MockTransport."""

from __future__ import annotations

import shutil
from pathlib import Path

import httpx


URLS = [
    "https://localhost/local-demo",
    "https://127.0.0.1/loopback-demo",
    "https://evil.malware.test/blocked-demo?token=synthetic-domain-demo",
    "https://api.unknown.test/warn-demo",
    "https://unlisted.example.test/unknown-demo",
    "http://unlisted.example.test/insecure-demo",
]


def main() -> None:
    shutil.copyfile(Path("examples/policy.yaml"), Path("policy.yaml"))

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"offline": True}, request=request)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        for url in URLS:
            headers = {"Authorization": "Bearer synthetic-domain-demo"} if "malware.test" in url else None
            response = client.get(url, headers=headers)
            print(f"offline domain demo: {response.request.url.host} -> {response.status_code}")


if __name__ == "__main__":
    main()
