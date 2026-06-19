"""Cross-platform local-only demo for TraceSeal httpx interception."""

from __future__ import annotations

import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx


SECRET_TOKEN = "SECRET_TOKEN_SHOULD_NOT_APPEAR"
API_KEY = "API_KEY_SHOULD_NOT_APPEAR"
BODY_SECRET = "BODY_SHOULD_NOT_APPEAR"


class DemoHandler(BaseHTTPRequestHandler):
    def _reply(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            self.rfile.read(length)
        payload = json.dumps({"ok": True, "response_secret": "RESPONSE_SHOULD_NOT_APPEAR"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Set-Cookie", "server-secret=RESPONSE_COOKIE_SHOULD_NOT_APPEAR")
        self.end_headers()
        self.wfile.write(payload)

    do_GET = _reply
    do_POST = _reply
    do_PUT = _reply
    do_PATCH = _reply
    do_DELETE = _reply

    def log_message(self, _format: str, *_args: object) -> None:
        return


async def run_async_requests(base_url: str) -> int:
    async with httpx.AsyncClient(base_url=base_url) as client:
        responses = [
            await client.get("/async/get"),
            await client.post("/async/post", json={"secret": BODY_SECRET}),
            await client.put("/async/put"),
            await client.patch("/async/patch"),
            await client.delete("/async/delete"),
            await client.request("GET", "/async/request"),
        ]
    return len(responses)


def main() -> None:
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    os.environ["no_proxy"] = "127.0.0.1,localhost"
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        functional = [
            httpx.get(f"{base_url}/function/get"),
            httpx.post(
                f"{base_url}/function/post",
                params={
                    "token": SECRET_TOKEN,
                    "access_token": SECRET_TOKEN,
                    "refresh_token": SECRET_TOKEN,
                    "api_key": API_KEY,
                    "apikey": API_KEY,
                    "key": API_KEY,
                    "secret": SECRET_TOKEN,
                    "client_secret": SECRET_TOKEN,
                    "password": SECRET_TOKEN,
                    "passwd": SECRET_TOKEN,
                    "auth": SECRET_TOKEN,
                    "authorization": SECRET_TOKEN,
                    "signature": SECRET_TOKEN,
                    "sig": SECRET_TOKEN,
                    "session": SECRET_TOKEN,
                    "cookie": SECRET_TOKEN,
                    "credential": SECRET_TOKEN,
                    "safe": "visible-demo-value",
                },
                headers={
                    "Authorization": f"Bearer {SECRET_TOKEN}",
                    "Proxy-Authorization": f"Bearer {SECRET_TOKEN}",
                    "Cookie": f"session={SECRET_TOKEN}",
                    "Set-Cookie": f"session={SECRET_TOKEN}",
                    "X-API-Key": API_KEY,
                    "X-Auth-Token": SECRET_TOKEN,
                    "X-CSRF-Token": SECRET_TOKEN,
                    "X-Demo": "visible-demo-value",
                },
                json={"secret": BODY_SECRET},
            ),
            httpx.put(f"{base_url}/function/put"),
            httpx.patch(f"{base_url}/function/patch"),
            httpx.delete(f"{base_url}/function/delete"),
            httpx.request("GET", f"{base_url}/function/request"),
        ]

        with httpx.Client(base_url=base_url) as client:
            client_responses = [
                client.get("/client/get"),
                client.post("/client/post", content=BODY_SECRET),
                client.put("/client/put"),
                client.patch("/client/patch"),
                client.delete("/client/delete"),
                client.request("GET", "/client/request"),
            ]

        async_count = asyncio.run(run_async_requests(base_url))

        def timeout_transport(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("synthetic timeout", request=request)

        try:
            with httpx.Client(transport=httpx.MockTransport(timeout_transport)) as timeout_client:
                timeout_client.get("https://timeout.invalid/demo", timeout=0.01)
        except httpx.ReadTimeout:
            print("synthetic timeout recorded")

        def connection_transport(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("synthetic connection error", request=request)

        try:
            with httpx.Client(transport=httpx.MockTransport(connection_transport)) as connection_client:
                connection_client.get("https://connection.invalid/demo")
        except httpx.ConnectError:
            print("connection error recorded")

        try:
            httpx.get("://invalid url")
        except httpx.HTTPError:
            print("invalid URL recorded")

        print("httpx responses:", len(functional), len(client_responses), async_count)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
