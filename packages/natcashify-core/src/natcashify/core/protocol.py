import json
import re
import time
import uuid
from collections.abc import Mapping, Sequence
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Final, cast
from urllib.parse import urlsplit

from natcashify.core.config import MerchantConfig
from natcashify.core.errors import (
    APIError,
    InvalidPaymentError,
    InvalidSignatureError,
    TransactionNotFoundError,
)
from natcashify.core.http import HttpRequest, HttpResponse
from natcashify.core.models import Callback, Payment, Transaction, TransactionStatus
from natcashify.core.signing import (
    callback_signature,
    payment_signature,
    signatures_match,
    transaction_signature,
    validate_amount,
    wire_amount,
)

LIVE_URL: Final = "https://merchantpay.natcom.com.ht/api/online-payment/"
SANDBOX_URL: Final = "https://testmerchantpay.natcom.com.ht/api/online-payment/"
PAYMENT_PATH: Final = "credential"
TRANSACTION_PATH: Final = "merchant/checkTransaction"
DEFAULT_TIMEOUT: Final = 10.0

_PHONE: Final = re.compile(r"509[0-9]{8}")
_INTEGER: Final = re.compile(r"-?[0-9]{1,9}")
_MAX_EXPIRY_SECONDS: Final = 315_360_000
_MAX_CODE: Final = 999_999_999
_NOT_FOUND_STATUS: Final = 101
_HEADERS: Final = {"Content-Type": "application/json", "Accept": "application/json"}


def new_request_id() -> str:
    return str(uuid.uuid4())


def now_ms() -> int:
    return time.time_ns() // 1_000_000


def validate_payment(
    order_number: str,
    amount: Decimal | int,
    phone_number: str | None,
    *,
    skip_phone_input: bool,
) -> Decimal:
    if not order_number:
        raise InvalidPaymentError("order_number must not be empty")
    validated = validate_amount(amount)
    if phone_number is None:
        if skip_phone_input:
            raise InvalidPaymentError("skip_phone_input requires a phone_number")
    elif not isinstance(phone_number, str) or not _PHONE.fullmatch(phone_number):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidPaymentError("phone_number must match 509 followed by 8 digits")
    return validated


def _post(url: str, timeout: float, body: Mapping[str, object]) -> HttpRequest:
    return HttpRequest(
        method="POST",
        url=url,
        headers=dict(_HEADERS),
        body=json.dumps(body, separators=(",", ":")).encode(),
        timeout=timeout,
    )


def build_payment_request(
    config: MerchantConfig,
    *,
    base_url: str,
    timeout: float,
    order_number: str,
    amount: Decimal,
    phone_number: str | None,
    skip_phone_input: bool,
    request_id: str,
    timestamp: int,
) -> HttpRequest:
    validated = validate_payment(
        order_number, amount, phone_number, skip_phone_input=skip_phone_input
    )
    body: dict[str, object] = {
        "partnerCode": config.partner_code,
        "username": config.username,
        "password": config.password,
        "callbackUrl": config.callback_url,
        "enableFee": config.payer_pays_fee,
        "language": config.language.value,
        "orderNumber": order_number,
        "amount": wire_amount(validated),
        "timestamp": timestamp,
        "requestId": request_id,
        "skipPhoneInput": skip_phone_input,
    }
    if phone_number is not None:
        body["msisdn"] = phone_number
    body["signature"] = payment_signature(
        config,
        request_id=request_id,
        timestamp=timestamp,
        order_number=order_number,
        amount=validated,
    )
    return _post(base_url + PAYMENT_PATH, timeout, body)


def build_transaction_request(
    config: MerchantConfig,
    *,
    base_url: str,
    timeout: float,
    order_number: str,
    request_id: str,
) -> HttpRequest:
    if not order_number:
        raise InvalidPaymentError("order_number must not be empty")
    body: dict[str, object] = {
        "requestId": request_id,
        "username": config.username,
        "password": config.password,
        "partnerCode": config.partner_code,
        "orderNumber": order_number,
        "signature": transaction_signature(
            config, order_number=order_number, request_id=request_id
        ),
    }
    return _post(base_url + TRANSACTION_PATH, timeout, body)


def _as_object_dict(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in cast("dict[object, object]", value).items()}


def _decode(response: HttpResponse) -> dict[str, object] | None:
    try:
        decoded: object = json.loads(response.body)
    except (ValueError, RecursionError):
        return None
    return _as_object_dict(decoded)


def _envelope(response: HttpResponse) -> dict[str, object]:
    http_ok = 200 <= response.status < 300
    payload = _decode(response)
    if payload is None:
        reason = "unexpected response body" if http_ok else "HTTP error"
        raise APIError(f"NatCash API returned {reason}", http_status=response.status)
    status = payload.get("status")
    if isinstance(status, bool) or not isinstance(status, int):
        raise APIError("NatCash API response has no valid status", http_status=response.status)
    code = payload.get("code")
    message = payload.get("message")
    if status != 0 or not http_ok:
        error_type = TransactionNotFoundError if status == _NOT_FOUND_STATUS else APIError
        raise error_type(
            message if isinstance(message, str) and message else "NatCash API error",
            status=status,
            code=code if isinstance(code, str) else None,
            http_status=response.status,
        )
    return payload


def _malformed(response: HttpResponse, what: str) -> APIError:
    return APIError(f"NatCash API response has invalid {what}", http_status=response.status)


def _is_http_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    return parts.scheme in {"http", "https"} and bool(parts.netloc)


def _number(value: object) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return value


def parse_payment_response(
    response: HttpResponse, *, order_number: str, request_id: str
) -> Payment:
    payload = _envelope(response)
    url = payload.get("url")
    if not isinstance(url, str) or not _is_http_url(url):
        raise _malformed(response, "url")
    seconds = _number(payload.get("expiredAt"))
    if seconds is None or not 0 <= seconds <= _MAX_EXPIRY_SECONDS:
        raise _malformed(response, "expiredAt")
    return Payment(url, timedelta(seconds=seconds), order_number, request_id)


def _text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return None


def _parse_amount(value: object) -> Decimal | None:
    number = _number(value)
    raw = str(number) if number is not None else value
    if not isinstance(raw, str):
        return None
    try:
        amount = Decimal(raw.replace(",", ""))
    except InvalidOperation:
        return None
    return amount if amount.is_finite() else None


def _response_code(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if abs(value) <= _MAX_CODE else None
    if isinstance(value, str) and _INTEGER.fullmatch(value):
        return int(value)
    return None


def parse_transaction_response(response: HttpResponse) -> Transaction:
    fields = _as_object_dict(_envelope(response).get("data"))
    if fields is None:
        raise _malformed(response, "data")
    order_number = _text(fields.get("orderNumber"))
    transaction_id = _text(fields.get("transId"))
    amount = _parse_amount(fields.get("amount"))
    if order_number is None:
        raise _malformed(response, "orderNumber")
    if transaction_id is None:
        raise _malformed(response, "transId")
    if amount is None:
        raise _malformed(response, "amount")
    response_code = _response_code(fields.get("responseCode"))
    return Transaction(
        order_number=order_number,
        transaction_id=transaction_id,
        amount=amount,
        payer=_text(fields.get("toPhone")) or "",
        status=TransactionStatus.from_code(response_code),
        response_code=response_code,
    )


def verify_callback(config: MerchantConfig, order_number: str, code: int, signature: str) -> bool:
    expected = callback_signature(config, order_number=order_number, code=code)
    return signatures_match(expected, signature)


def _single(params: Mapping[str, str | Sequence[str]], key: str) -> str:
    value = params.get(key)
    if isinstance(value, str):
        return value
    if isinstance(value, Sequence) and len(value) == 1 and isinstance(value[0], str):  # pyright: ignore[reportUnnecessaryIsInstance]
        return value[0]
    raise InvalidSignatureError(f"Callback parameter {key} is missing or repeated")


def parse_callback(config: MerchantConfig, params: Mapping[str, str | Sequence[str]]) -> Callback:
    order_number = _single(params, "orderNumber")
    raw_code = _single(params, "code")
    signature = _single(params, "signature")
    if not _INTEGER.fullmatch(raw_code) or str(int(raw_code)) != raw_code:
        raise InvalidSignatureError("Callback code is not an integer")
    code = int(raw_code)
    if not verify_callback(config, order_number, code, signature):
        raise InvalidSignatureError("Callback signature does not match")
    return Callback(order_number, code, TransactionStatus.from_code(code))
