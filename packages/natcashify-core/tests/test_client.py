import json
import logging
from decimal import Decimal
from typing import Any

import pytest
from php_vectors import CONFIG

from natcashify.core.client import NatcashClient
from natcashify.core.errors import (
    APIError,
    ConfigurationError,
    InvalidPaymentError,
    InvalidSignatureError,
    TransactionNotFoundError,
)
from natcashify.core.protocol import DEFAULT_TIMEOUT, LIVE_URL, SANDBOX_URL
from natcashify.core.testing import FakeTransport, json_response

PAYMENT_OK: dict[str, Any] = {
    "status": 0,
    "code": "00",
    "message": "ok",
    "url": "https://pay.example/checkout/abc",
    "expiredAt": 900,
}


def transaction_ok(order_number: str = "O1") -> dict[str, Any]:
    return {
        "status": 0,
        "code": "00",
        "message": "ok",
        "data": {
            "orderNumber": order_number,
            "transId": "T1",
            "amount": "3,162.00",
            "toPhone": "50912345678",
            "responseCode": 1,
        },
    }


ENV = {
    "NATCASH_PRIVATE_KEY": "pk",
    "NATCASH_PARTNER_CODE": "pc",
    "NATCASH_FUNCTION_CODE": "fc",
    "NATCASH_USERNAME": "user",
    "NATCASH_PASSWORD": "pw",
    "NATCASH_CALLBACK_URL": "https://shop.example/cb",
}


def test_create_payment_posts_to_the_sandbox_by_default() -> None:
    transport = FakeTransport(json_response(PAYMENT_OK))
    payment = NatcashClient(CONFIG, transport=transport).create_payment("O1", Decimal("250"))
    assert transport.requests[0].url == SANDBOX_URL + "credential"
    assert payment.checkout_url == PAYMENT_OK["url"]
    assert payment.request_id == json.loads(transport.requests[0].body)["requestId"]


def test_live_mode_uses_the_live_url() -> None:
    transport = FakeTransport(json_response(PAYMENT_OK))
    client = NatcashClient(CONFIG, sandbox=False, transport=transport)
    client.create_payment("O1", 250)
    assert transport.requests[0].url == LIVE_URL + "credential"
    assert client.sandbox is False
    assert client.config is CONFIG


def test_each_payment_gets_a_fresh_request_id() -> None:
    transport = FakeTransport(json_response(PAYMENT_OK), json_response(PAYMENT_OK))
    client = NatcashClient(CONFIG, transport=transport)
    first = client.create_payment("O1", 250)
    second = client.create_payment("O1", 250)
    assert first.request_id != second.request_id


def test_invalid_payment_does_no_io() -> None:
    transport = FakeTransport()
    with pytest.raises(InvalidPaymentError):
        NatcashClient(CONFIG, transport=transport).create_payment("O1", Decimal("0"))
    assert transport.requests == []


def test_get_transaction_reuses_a_given_request_id() -> None:
    transport = FakeTransport(json_response(transaction_ok()))
    transaction = NatcashClient(CONFIG, transport=transport).get_transaction(
        "O1", request_id="fixed-id"
    )
    assert json.loads(transport.requests[0].body)["requestId"] == "fixed-id"
    assert transport.requests[0].url == SANDBOX_URL + "merchant/checkTransaction"
    assert transaction.is_successful
    assert transaction.amount == Decimal("3162.00")


def test_get_transaction_generates_a_request_id_by_default() -> None:
    transport = FakeTransport(json_response(transaction_ok()))
    NatcashClient(CONFIG, transport=transport).get_transaction("O1")
    assert json.loads(transport.requests[0].body)["requestId"]


def test_get_transaction_rejects_a_different_order() -> None:
    transport = FakeTransport(json_response(transaction_ok("OTHER")))
    with pytest.raises(APIError) as error:
        NatcashClient(CONFIG, transport=transport).get_transaction("O1")
    assert CONFIG.password not in str(error.value)
    assert CONFIG.private_key not in str(error.value)


def test_get_transaction_not_found() -> None:
    transport = FakeTransport(json_response({"status": 101, "message": "nope"}))
    with pytest.raises(TransactionNotFoundError):
        NatcashClient(CONFIG, transport=transport).get_transaction("O1")


def test_timeout_is_forwarded() -> None:
    transport = FakeTransport(json_response(PAYMENT_OK), json_response(transaction_ok()))
    client = NatcashClient(CONFIG, timeout=2.5, transport=transport)
    client.create_payment("O1", 250)
    client.get_transaction("O1")
    assert [request.timeout for request in transport.requests] == [2.5, 2.5]


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_timeout_is_rejected(timeout: float) -> None:
    with pytest.raises(ConfigurationError):
        NatcashClient(CONFIG, timeout=timeout, transport=FakeTransport())


def test_verify_and_parse_callback() -> None:
    from natcashify.core.signing import callback_signature

    client = NatcashClient(CONFIG, transport=FakeTransport())
    signature = callback_signature(CONFIG, order_number="O1", code=1)
    assert client.verify_callback("O1", 1, signature)
    assert not client.verify_callback("O1", -1, signature)
    callback = client.parse_callback({"orderNumber": "O1", "code": "1", "signature": signature})
    assert callback.is_successful
    with pytest.raises(InvalidSignatureError):
        client.parse_callback({"orderNumber": "O1", "code": "1", "signature": "bad"})


def test_from_env_defaults_to_sandbox() -> None:
    client = NatcashClient.from_env(environ=ENV, transport=FakeTransport())
    assert client.sandbox is True
    assert client.config.partner_code == "pc"


def test_from_env_reads_sandbox_and_timeout() -> None:
    transport = FakeTransport(json_response(PAYMENT_OK))
    environ = {**ENV, "NATCASH_SANDBOX": "false", "NATCASH_TIMEOUT": "2.5"}
    client = NatcashClient.from_env(environ=environ, transport=transport)
    client.create_payment("O1", 250)
    assert client.sandbox is False
    assert transport.requests[0].url == LIVE_URL + "credential"
    assert transport.requests[0].timeout == 2.5


def test_from_env_uses_the_default_timeout() -> None:
    transport = FakeTransport(json_response(PAYMENT_OK))
    NatcashClient.from_env(environ=ENV, transport=transport).create_payment("O1", 250)
    assert transport.requests[0].timeout == DEFAULT_TIMEOUT


def test_from_env_uses_the_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    assert NatcashClient.from_env(transport=FakeTransport()).config.username == "user"


def test_from_env_supports_a_prefix() -> None:
    environ = {key.replace("NATCASH_", "ACME_"): value for key, value in ENV.items()}
    environ["ACME_SANDBOX"] = "0"
    client = NatcashClient.from_env("ACME_", environ, transport=FakeTransport())
    assert client.sandbox is False


@pytest.mark.parametrize("value", ["0", "-1", "abc", "nan", "inf", ""])
def test_from_env_rejects_a_bad_timeout_naming_the_variable(value: str) -> None:
    with pytest.raises(ConfigurationError, match="NATCASH_TIMEOUT") as error:
        NatcashClient.from_env(environ={**ENV, "NATCASH_TIMEOUT": value})
    assert ENV["NATCASH_PASSWORD"] not in str(error.value)


def test_from_env_rejects_a_bad_sandbox_flag() -> None:
    with pytest.raises(ConfigurationError, match="NATCASH_SANDBOX"):
        NatcashClient.from_env(environ={**ENV, "NATCASH_SANDBOX": "maybe"})


def test_logs_never_contain_secrets(caplog: pytest.LogCaptureFixture) -> None:
    transport = FakeTransport(json_response(PAYMENT_OK), json_response(transaction_ok()))
    client = NatcashClient(CONFIG, transport=transport)
    with caplog.at_level(logging.DEBUG, logger="natcashify"):
        client.create_payment("O1", 250)
        client.get_transaction("O1")
    text = caplog.text
    assert "O1" in text
    assert "http_status=200" in text
    bodies = [json.loads(request.body) for request in transport.requests]
    secrets = [CONFIG.password, CONFIG.private_key, CONFIG.function_code]
    secrets += [body["signature"] for body in bodies]
    secrets += [request.body.decode() for request in transport.requests]
    assert not any(secret in text for secret in secrets)


class ClosableTransport(FakeTransport):
    closed = False

    def close(self) -> None:
        self.closed = True


def test_close_calls_transport_close() -> None:
    transport = ClosableTransport()
    with NatcashClient(CONFIG, transport=transport):
        assert not transport.closed
    assert transport.closed


def test_close_without_transport_close_is_a_no_op() -> None:
    NatcashClient(CONFIG, transport=FakeTransport()).close()


@pytest.mark.parametrize("sandbox", [None, "false", "true", 0, 1])
def test_non_boolean_sandbox_is_rejected(sandbox: Any) -> None:
    with pytest.raises(ConfigurationError, match="sandbox"):
        NatcashClient(CONFIG, sandbox=sandbox, transport=FakeTransport())


@pytest.mark.parametrize("timeout", [None, "5", object()])
def test_non_numeric_timeout_raises_a_configuration_error(timeout: Any) -> None:
    with pytest.raises(ConfigurationError, match="timeout"):
        NatcashClient(CONFIG, timeout=timeout, transport=FakeTransport())
