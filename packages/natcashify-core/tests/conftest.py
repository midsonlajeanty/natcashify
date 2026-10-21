import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar

import pytest

SLOW_DELAY_SECONDS = 1.0


@dataclass
class LocalServer:
    base_url: str
    hits: list[str] = field(default_factory=list[str])


def _serve(handler_factory: type[BaseHTTPRequestHandler]) -> Iterator[LocalServer]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_factory)
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()
    host, port = server.server_address[:2]
    local = LocalServer(f"http://{host!s}:{port}")
    handler_factory.hits = local.hits  # type: ignore[attr-defined]
    try:
        yield local
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class _Handler(BaseHTTPRequestHandler):
    hits: ClassVar[list[str]] = []

    def do_POST(self) -> None:
        self.hits.append(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/target")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path in {"/truncated", "/truncated-error"}:
            self.send_response(200 if self.path == "/truncated" else 500)
            self.send_header("Content-Length", "100")
            self.end_headers()
            self.wfile.write(b"short")
            return
        body = b'{"error": "boom"}'
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return None


class _SlowHandler(_Handler):
    release: ClassVar[threading.Event]

    def do_POST(self) -> None:
        self.release.wait(timeout=SLOW_DELAY_SECONDS)
        super().do_POST()


@pytest.fixture
def local_server() -> Iterator[LocalServer]:
    yield from _serve(type("Handler", (_Handler,), {}))


@pytest.fixture
def slow_server() -> Iterator[LocalServer]:
    release = threading.Event()
    handler = type("SlowHandler", (_SlowHandler,), {"release": release})
    served = _serve(handler)
    try:
        yield next(served)
    finally:
        release.set()
        next(served, None)
