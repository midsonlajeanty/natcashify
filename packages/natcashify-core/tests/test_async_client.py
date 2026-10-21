import json
from decimal import Decimal
from typing import Any

import pytest
from php_vectors import CONFIG
from test_client import ENV, PAYMENT_OK, transaction_ok

from natcashify.core.client import AsyncNatcashClient
from natcashify.core.errors import APIError, ConfigurationError, InvalidPaymentError
from natcashify.core.protocol import LIVE_URL, SANDBOX_URL
from natcashify.core.testing import AsyncFakeTransport, json_response, sign_callback


async def test_create_payment_posts_to_the_sandbox_by_default() -> None:
    transport = AsyncFakeTransport(json_response(PAYMENT_OK))
    async with AsyncNatcashClient(CONFIG, transport=transport) as client:
        payment = await client.create_payment("O1", Decimal("250"))
    assert transport.requests[0].url == SANDBOX_URL + "credential"
    assert payment.checkout_url == PAYMENT_OK["url"]
    assert payment.request_id == json.loads(transport.requests[0].body)["requestId"]


async def test_live_mode_uses_the_live_url() -> None:
    transport = AsyncFakeTransport(json_response(PAYMENT_OK))
    await AsyncNatcashClient(CONFIG, sandbox=False, transport=transport).create_payment("O1", 250)
    assert transport.requests[0].url == LIVE_URL + "credential"


async def test_each_payment_gets_a_fresh_request_id() -> None:
    transport = AsyncFakeTransport(json_response(PAYMENT_OK), json_response(PAYMENT_OK))
    client = AsyncNatcashClient(CONFIG, transport=transport)
    first = await client.create_payment("O1", 250)
    second = await client.create_payment("O1", 250)
    assert first.request_id != second.request_id


async def test_invalid_payment_does_no_io() -> None:
    transport = AsyncFakeTransport()
    with pytest.raises(InvalidPaymentError):
        await AsyncNatcashClient(CONFIG, transport=transport).create_payment("O1", 0)
    assert transport.requests == []


async def test_get_transaction_reuses_a_given_request_id() -> None:
    transport = AsyncFakeTransport(json_response(transaction_ok()))
    client = AsyncNatcashClient(CONFIG, timeout=3.0, transport=transport)
    transaction = await client.get_transaction("O1", request_id="fixed-id")
    assert json.loads(transport.requests[0].body)["requestId"] == "fixed-id"
    assert transport.requests[0].timeout == 3.0
    assert transaction.is_successful


async def test_get_transaction_rejects_a_different_order() -> None:
    transport = AsyncFakeTransport(json_response(transaction_ok("OTHER")))
    with pytest.raises(APIError) as error:
        await AsyncNatcashClient(CONFIG, transport=transport).get_transaction("O1")
    assert CONFIG.password not in str(error.value)


async def test_callbacks_are_synchronous() -> None:
    client = AsyncNatcashClient(CONFIG, transport=AsyncFakeTransport())
    signature = sign_callback(CONFIG, "O1", 1)
    assert client.verify_callback("O1", 1, signature)
    params = {"orderNumber": "O1", "code": "1", "signature": signature}
    assert client.parse_callback(params).is_successful


def test_from_env_reads_sandbox_and_timeout() -> None:
    environ = {**ENV, "NATCASH_SANDBOX": "false", "NATCASH_TIMEOUT": "2.5"}
    client = AsyncNatcashClient.from_env(environ=environ, transport=AsyncFakeTransport())
    assert client.sandbox is False
    with pytest.raises(ConfigurationError, match="NATCASH_TIMEOUT"):
        AsyncNatcashClient.from_env(environ={**ENV, "NATCASH_TIMEOUT": "0"})


class ClosableTransport(AsyncFakeTransport):
    closed = False

    async def aclose(self) -> None:
        self.closed = True


async def test_aclose_calls_transport_aclose() -> None:
    transport = ClosableTransport()
    async with AsyncNatcashClient(CONFIG, transport=transport):
        assert not transport.closed
    assert transport.closed


async def test_aclose_without_transport_aclose_is_a_no_op() -> None:
    await AsyncNatcashClient(CONFIG, transport=AsyncFakeTransport()).aclose()


@pytest.mark.parametrize("sandbox", [None, "false", 0])
def test_async_client_rejects_a_non_boolean_sandbox(sandbox: Any) -> None:
    with pytest.raises(ConfigurationError, match="sandbox"):
        AsyncNatcashClient(CONFIG, sandbox=sandbox, transport=AsyncFakeTransport())
