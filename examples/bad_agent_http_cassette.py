"""Local-only demo for redacted HTTP cassette generation."""

from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx


FAKE_TOKEN = "FAKE_TOKEN_FOR_CASSETTE_DEMO"
FAKE_API_KEY = "FAKE_API_KEY_FOR_CASSETTE_DEMO"
FAKE_PASSWORD = "FAKE_PASSWORD_FOR_CASSETTE_DEMO"
FAKE_BODY = "FAKE_REQUEST_BODY_NOT_STORED"


class DemoHandler(BaseHTTPRequestHandler):
    def _reply(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            self.rfile.read(length)
        payload = json.dumps({"ok": True, "secret": "FAKE_RESPONSE_BODY_NOT_STORED"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Set-Cookie", "session=FAKE_RESPONSE_COOKIE_NOT_STORED")
        self.send_header("X-Response-Secret", "FAKE_RESPONSE_HEADER_NOT_STORED")
        self.end_headers()
        self.wfile.write(payload)

    do_GET = _reply
    do_POST = _reply

    def log_message(self, _format: str, *_args: object) -> None:
        return


def main() -> None:
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    os.environ["no_proxy"] = "127.0.0.1,localhost"
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        get_response = httpx.get(f"{base_url}/audit/get", params={"page": "1", "view": "compact"})
        post_response = httpx.post(
            f"{base_url}/audit/post",
            params={
                "token": FAKE_TOKEN,
                "api_key": FAKE_API_KEY,
                "password": FAKE_PASSWORD,
                "safe": "visible-demo-value",
            },
            headers={
                "Authorization": f"Bearer {FAKE_TOKEN}",
                "X-API-Key": FAKE_API_KEY,
                "X-Credential-Session": FAKE_TOKEN,
                "X-Demo": "visible-demo-value",
            },
            json={"password": FAKE_BODY},
        )
        print("cassette demo status:", get_response.status_code, post_response.status_code)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
