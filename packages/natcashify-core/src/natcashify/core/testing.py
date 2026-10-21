import json
from collections import deque

from natcashify.core.config import MerchantConfig
from natcashify.core.http import HttpRequest, HttpResponse
from natcashify.core.signing import callback_signature


def json_response(payload: object, status: int = 200) -> HttpResponse:
    return HttpResponse(status, {"Content-Type": "application/json"}, json.dumps(payload).encode())


def sign_callback(config: MerchantConfig, order_number: str, code: int) -> str:
    return callback_signature(config, order_number=order_number, code=code)


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
