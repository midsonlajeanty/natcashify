import json

import pytest

from natcashify.core.http import HttpRequest
from natcashify.core.testing import AsyncFakeTransport, FakeTransport, json_response

REQUEST = HttpRequest("POST", "https://example.test/api", {}, b"{}", 5.0)


def test_fake_transport_records_and_replays() -> None:
    first, second = json_response({"a": 1}), json_response({"b": 2}, status=400)
    transport = FakeTransport(first, second)
    assert transport.send(REQUEST) is first
    assert transport.send(REQUEST) is second
    assert transport.requests == [REQUEST, REQUEST]
    with pytest.raises(AssertionError):
        transport.send(REQUEST)


async def test_async_fake_transport_records_and_replays() -> None:
    response = json_response({"a": 1})
    transport = AsyncFakeTransport(response)
    assert await transport.send(REQUEST) is response
    assert transport.requests == [REQUEST]
    with pytest.raises(AssertionError):
        await transport.send(REQUEST)


def test_json_response_encodes_the_payload() -> None:
    response = json_response({"a": 1}, status=201)
    assert response.status == 201
    assert json.loads(response.body) == {"a": 1}
    assert response.headers["Content-Type"] == "application/json"
