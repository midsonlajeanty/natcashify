import asyncio
import http.client
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from email.message import Message
from importlib.metadata import PackageNotFoundError, version
from typing import IO, Final, Protocol, override
from urllib.parse import urlsplit

from natcashify.core.errors import TransportError


def _distribution_version() -> str:
    try:
        return version("natcashify-core")
    except PackageNotFoundError:
        return "unknown"


USER_AGENT: Final[str] = f"natcashify/{_distribution_version()}"
ALLOWED_SCHEMES: Final = frozenset({"http", "https"})


@dataclass(frozen=True, slots=True)
class HttpRequest:
    method: str
    url: str
    headers: Mapping[str, str]
    body: bytes = field(repr=False)
    timeout: float


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes

    def header(self, name: str) -> str | None:
        wanted = name.lower()
        return next((v for k, v in self.headers.items() if k.lower() == wanted), None)


class HttpTransport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse: ...


class AsyncHttpTransport(Protocol):
    async def send(self, request: HttpRequest) -> HttpResponse: ...


def _require_http_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_SCHEMES or not parts.netloc:
        raise TransportError("Only absolute http and https URLs are allowed")


def _with_user_agent(headers: Mapping[str, str]) -> dict[str, str]:
    # urllib's default "Python-urllib" agent is rejected by some bot-protected endpoints.
    if any(name.lower() == "user-agent" for name in headers):
        return dict(headers)
    return {**headers, "User-Agent": USER_AGENT}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # urllib would replay a POST as a bodiless GET and forward signature headers to any host.
    @override
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> None:
        return None


class UrllibTransport:
    def __init__(self) -> None:
        self._opener = urllib.request.build_opener(_NoRedirect)

    def send(self, request: HttpRequest) -> HttpResponse:
        try:
            _require_http_url(request.url)
            return self._perform(request)
        except urllib.error.URLError as error:
            cause = error.reason if isinstance(error.reason, OSError) else error
            raise TransportError(f"HTTP request failed: {error.reason}") from cause
        except (OSError, http.client.HTTPException, ValueError) as error:
            raise TransportError(f"HTTP request failed: {error}") from error

    def _perform(self, request: HttpRequest) -> HttpResponse:
        prepared = urllib.request.Request(  # noqa: S310 (scheme checked by _require_http_url)
            request.url,
            data=request.body,
            headers=_with_user_agent(request.headers),
            method=request.method,
        )
        try:
            with self._opener.open(prepared, timeout=request.timeout) as response:
                return HttpResponse(
                    response.status, dict(response.headers.items()), response.read()
                )
        except urllib.error.HTTPError as error:
            with error:
                return HttpResponse(error.code, dict(error.headers.items()), error.read())


class AsyncUrllibTransport:
    def __init__(self, inner: HttpTransport | None = None) -> None:
        self._inner: HttpTransport = inner if inner is not None else UrllibTransport()

    async def send(self, request: HttpRequest) -> HttpResponse:
        return await asyncio.to_thread(self._inner.send, request)
