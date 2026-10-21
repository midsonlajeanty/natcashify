import json
from collections import deque

from natcashify.core.http import HttpRequest, HttpResponse


def json_response(payload: object, status: int = 200) -> HttpResponse:
    return HttpResponse(status, {"Content-Type": "application/json"}, json.dumps(payload).encode())


class FakeTransport:
    def __init__(self, *responses: HttpResponse) -> None:
        self._responses = deque(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        if not self._responses:
            raise AssertionError("FakeTransport has no queued response left")
        return self._responses.popleft()


class AsyncFakeTransport:
    def __init__(self, *responses: HttpResponse) -> None:
        self._inner = FakeTransport(*responses)

    @property
    def requests(self) -> list[HttpRequest]:
        return self._inner.requests

    async def send(self, request: HttpRequest) -> HttpResponse:
        return self._inner.send(request)
