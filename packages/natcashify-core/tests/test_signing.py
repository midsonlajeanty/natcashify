from decimal import Decimal
from typing import Any

import pytest
from php_vectors import CONFIG, VECTORS, config_for

from natcashify.core.errors import InvalidPaymentError
from natcashify.core.signing import (
    MAX_AMOUNT,
    callback_signature,
    format_amount,
    payment_signature,
    signatures_match,
    transaction_signature,
    validate_amount,
    wire_amount,
)


@pytest.mark.parametrize("case", VECTORS["payments"], ids=lambda c: c["inputs"]["orderNumber"])
def test_payment_signature_matches_php(case: dict[str, Any]) -> None:
    payload = case["payload"]
    signature = payment_signature(
        config_for(case),
        request_id=payload["requestId"],
        timestamp=payload["timestamp"],
        order_number=payload["orderNumber"],
        amount=Decimal(case["inputs"]["amount"]),
    )
    assert signature == payload["signature"]


@pytest.mark.parametrize("case", VECTORS["transactions"], ids=lambda c: c["inputs"]["orderNumber"])
def test_transaction_signature_matches_php(case: dict[str, Any]) -> None:
    payload = case["payload"]
    signature = transaction_signature(
        CONFIG, order_number=payload["orderNumber"], request_id=payload["requestId"]
    )
    assert signature == payload["signature"]


@pytest.mark.parametrize("case", VECTORS["callbacks"], ids=lambda c: str(c["code"]))
def test_callback_signature_matches_php(case: dict[str, Any]) -> None:
    signature = callback_signature(CONFIG, order_number=case["order_number"], code=case["code"])
    assert signature == case["signature"]


@pytest.mark.parametrize("case", VECTORS["payments"], ids=lambda c: c["inputs"]["orderNumber"])
def test_amount_formats_match_php(case: dict[str, Any]) -> None:
    amount = validate_amount(Decimal(case["inputs"]["amount"]))
    assert format_amount(amount) == str(case["payload"]["amount"])


@pytest.mark.parametrize(
    ("amount", "text"),
    [
        (Decimal("100"), "100"),
        (Decimal("100.00"), "100"),
        (Decimal("10.10"), "10.1"),
        (Decimal("0.01"), "0.01"),
        (MAX_AMOUNT, "999999999.99"),
    ],
)
def test_format_amount_matches_php_float_strings(amount: Decimal, text: str) -> None:
    assert format_amount(amount) == text


def test_wire_amount_is_int_when_integral_else_float() -> None:
    integral = wire_amount(Decimal("100.00"))
    fractional = wire_amount(Decimal("10.10"))
    assert integral == 100
    assert isinstance(integral, int)
    assert fractional == 10.1
    assert isinstance(fractional, float)


@pytest.mark.parametrize(
    "amount",
    [
        0,
        -1,
        Decimal("0"),
        Decimal("10.555"),
        Decimal("1000000000"),
        Decimal("NaN"),
        Decimal("Infinity"),
        True,
        10.5,
        "10",
    ],
)
def test_invalid_amounts_are_rejected(amount: Any) -> None:
    with pytest.raises(InvalidPaymentError):
        validate_amount(amount)


def test_int_amounts_become_decimals() -> None:
    assert validate_amount(250) == Decimal(250)


def test_signatures_match_ignores_case_and_whitespace() -> None:
    assert signatures_match("ab12", " AB12\n")
    assert not signatures_match("ab12", "ab13")
