import hashlib
import hmac
from decimal import Decimal
from typing import Final

from natcashify.core.config import MerchantConfig
from natcashify.core.errors import InvalidPaymentError

MAX_AMOUNT: Final = Decimal("999999999.99")
_CENT: Final = Decimal("0.01")


def validate_amount(amount: Decimal | int) -> Decimal:
    if isinstance(amount, bool) or not isinstance(amount, Decimal | int):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidPaymentError(f"amount must be a Decimal or int, got {type(amount).__name__}")
    value = Decimal(amount)
    if not value.is_finite() or value <= 0:
        raise InvalidPaymentError("amount must be a positive number")
    if value > MAX_AMOUNT:
        raise InvalidPaymentError(f"amount must not exceed {MAX_AMOUNT}")
    if value != value.quantize(_CENT):
        raise InvalidPaymentError("amount must have at most two decimal places")
    return value


def format_amount(amount: Decimal) -> str:
    if amount == amount.to_integral_value():
        return str(int(amount))
    return format(amount.normalize(), "f")


def wire_amount(amount: Decimal) -> int | float:
    if amount == amount.to_integral_value():
        return int(amount)
    return float(amount)


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _hmac_hex(key: str, message: str) -> str:
    return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()


def payment_signature(
    config: MerchantConfig,
    *,
    request_id: str,
    timestamp: int,
    order_number: str,
    amount: Decimal,
) -> str:
    message = "".join(
        (
            _sha256_hex(config.private_key + request_id),
            config.partner_code,
            config.username,
            config.password,
            str(timestamp),
            request_id,
            order_number,
            format_amount(amount),
        )
    )
    return _hmac_hex(config.private_key, message)


def transaction_signature(config: MerchantConfig, *, order_number: str, request_id: str) -> str:
    message = "".join(
        (
            _sha256_hex(config.private_key + request_id),
            config.partner_code,
            config.username,
            config.password,
            order_number,
            request_id,
        )
    )
    return _hmac_hex(config.private_key, message)


def callback_signature(config: MerchantConfig, *, order_number: str, code: int) -> str:
    message = _sha256_hex(config.function_code + order_number) + order_number + str(code)
    return _hmac_hex(config.function_code, message)


def signatures_match(expected: str, received: str) -> bool:
    return hmac.compare_digest(expected.encode(), received.strip().lower().encode())
