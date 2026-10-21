import json
from typing import Any

import pytest
from php_vectors import CONFIG, VECTORS

from natcashify.core.http import HttpRequest
from natcashify.core.models import TransactionStatus
from natcashify.core.protocol import parse_callback
from natcashify.core.testing import (
    AsyncFakeTransport,
    FakeTransport,
    json_response,
    sign_callback,
)

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


@pytest.mark.parametrize("case", VECTORS["callbacks"], ids=lambda c: str(c["code"]))
def test_sign_callback_matches_the_php_sdk(case: dict[str, Any]) -> None:
    assert sign_callback(CONFIG, case["order_number"], case["code"]) == case["signature"]


def test_sign_callback_produces_a_verifiable_callback() -> None:
    signature = sign_callback(CONFIG, "O1", 1)
    callback = parse_callback(CONFIG, {"orderNumber": "O1", "code": "1", "signature": signature})
    assert callback.status is TransactionStatus.SUCCESS
