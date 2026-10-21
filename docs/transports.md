# Custom transports

The clients do their I/O through a transport. Two protocols are defined in the core:

```python
class HttpTransport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse: ...


class AsyncHttpTransport(Protocol):
    async def send(self, request: HttpRequest) -> HttpResponse: ...
```

`HttpRequest` has `method`, `url`, `headers`, `body` (bytes) and `timeout`. `HttpResponse` has
`status`, `headers`, `body` (bytes) and a case-insensitive `header(name)` helper.

`NatcashClient` defaults to `UrllibTransport`, and `AsyncNatcashClient` to `AsyncUrllibTransport`,
which runs it in `asyncio.to_thread`. `UrllibTransport` refuses redirects: a redirected POST would
carry credentials to another host. Both raise `TransportError` on network failures.

## Plugging in httpx

```python
import httpx

from natcashify import AsyncNatcashClient, HttpRequest, HttpResponse, TransportError


class HttpxTransport:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(follow_redirects=False)

    async def send(self, request: HttpRequest) -> HttpResponse:
        try:
            response = await self._client.request(
                request.method,
                request.url,
                headers=dict(request.headers),
                content=request.body,
                timeout=request.timeout,
            )
        except httpx.HTTPError as error:
            raise TransportError("NatCash request failed") from error
        return HttpResponse(response.status_code, dict(response.headers), response.content)

    async def aclose(self) -> None:
        await self._client.aclose()


client = AsyncNatcashClient(config, transport=HttpxTransport())
```

If the transport has a `close()` (sync) or `aclose()` (async) method, the client calls it from its
own `close()` or `aclose()`.

Follow the same rules as the built-in transport: do not follow redirects, honour
`request.timeout`, and wrap network failures in `TransportError`. Do not log request bodies, they
contain credentials.

## Fakes for tests

`natcashify.core.testing` provides `FakeTransport`, `AsyncFakeTransport` and `json_response`, see
[Getting started](getting-started.md#testing-your-own-code).
