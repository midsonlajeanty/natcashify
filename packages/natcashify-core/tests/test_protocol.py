import json
from datetime import timedelta
from decimal import Decimal
from typing import Any

import pytest
from php_vectors import CONFIG, RAW_VECTORS, VECTORS, config_for

from natcashify.core.errors import (
    APIError,
    InvalidPaymentError,
    InvalidSignatureError,
    TransactionNotFoundError,
)
from natcashify.core.http import HttpResponse
from natcashify.core.models import Callback, Payment, TransactionStatus
from natcashify.core.protocol import (
    LIVE_URL,
    SANDBOX_URL,
    build_payment_request,
    build_transaction_request,
    new_request_id,
    now_ms,
    parse_callback,
    parse_payment_response,
    parse_transaction_response,
    validate_payment,
    verify_callback,
)
from natcashify.core.signing import callback_signature
from natcashify.core.testing import json_response

PAYMENT_CASES = list(enumerate(VECTORS["payments"]))


def _payment_request(case: dict[str, Any], **overrides: Any) -> Any:
    inputs = case["inputs"]
    arguments: dict[str, Any] = {
        "base_url": SANDBOX_URL,
        "timeout": 10.0,
        "order_number": inputs["orderNumber"],
        "amount": Decimal(inputs["amount"]),
        "phone_number": inputs["msisdn"],
        "skip_phone_input": inputs["skipPhoneInput"],
        "request_id": case["payload"]["requestId"],
        "timestamp": inputs["timestamp"],
    }
    arguments.update(overrides)
    return build_payment_request(config_for(case), **arguments)


@pytest.mark.parametrize(("index", "case"), PAYMENT_CASES, ids=lambda v: str(v)[:12])
def test_payment_request_matches_the_php_payload(index: int, case: dict[str, Any]) -> None:
    request = _payment_request(case)
    assert request.method == "POST"
    assert request.url == SANDBOX_URL + "credential"
    assert request.timeout == 10.0
    assert json.loads(request.body) == RAW_VECTORS["payments"][index]["payload"]
    assert list(json.loads(request.body)) == list(RAW_VECTORS["payments"][index]["payload"])
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["Accept"] == "application/json"


@pytest.mark.parametrize(("index", "case"), list(enumerate(VECTORS["transactions"])))
def test_transaction_request_matches_the_php_payload(index: int, case: dict[str, Any]) -> None:
    request = build_transaction_request(
        CONFIG,
        base_url=LIVE_URL,
        timeout=5.0,
        order_number=case["inputs"]["orderNumber"],
        request_id=case["payload"]["requestId"],
    )
    assert request.url == LIVE_URL + "merchant/checkTransaction"
    assert json.loads(request.body) == RAW_VECTORS["transactions"][index]["payload"]
    assert request.headers["Content-Type"] == "application/json"


def test_payload_never_contains_private_key_or_function_code() -> None:
    request = _payment_request(VECTORS["payments"][0])
    assert CONFIG.private_key.encode() not in request.body
    assert CONFIG.function_code.encode() not in request.body
    body = json.loads(request.body)
    assert "privateKey" not in body
    assert "functionCode" not in body


def test_msisdn_is_omitted_when_absent() -> None:
    assert "msisdn" not in json.loads(_payment_request(VECTORS["payments"][0]).body)
    assert json.loads(_payment_request(VECTORS["payments"][6]).body)["msisdn"] == "50912345678"


@pytest.mark.parametrize(
    ("phone", "skip"),
    [
        ("5091234567", False),
        ("509\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668", False),
        (12345678901, False),
        ("40912345678", False),
        (None, True),
        ("", True),
        ("", False),
    ],
)
def test_invalid_phone_rules(phone: Any, skip: bool) -> None:
    with pytest.raises(InvalidPaymentError):
        validate_payment("O1", Decimal("5"), phone, skip_phone_input=skip)


def test_empty_order_number_is_rejected() -> None:
    with pytest.raises(InvalidPaymentError):
        validate_payment("", Decimal("5"), None, skip_phone_input=False)
    with pytest.raises(InvalidPaymentError):
        build_transaction_request(
            CONFIG, base_url=LIVE_URL, timeout=1.0, order_number="", request_id="r"
        )


def test_validate_payment_returns_the_validated_amount() -> None:
    assert validate_payment("O1", 5, "50912345678", skip_phone_input=True) == Decimal(5)


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-1"), Decimal("1.234"), Decimal("NaN")])
def test_build_payment_request_never_signs_an_unvalidated_amount(amount: Decimal) -> None:
    with pytest.raises(InvalidPaymentError):
        _payment_request(VECTORS["payments"][0], amount=amount)


def test_new_request_id_and_now_ms() -> None:
    assert new_request_id() != new_request_id()
    assert len(new_request_id()) == 36
    assert now_ms() > 1_700_000_000_000


def test_parse_payment_response() -> None:
    payment = parse_payment_response(
        json_response(
            {
                "status": 0,
                "code": "SUCCESS",
                "message": "Success",
                "url": "https://pay.example/x",
                "expiredAt": 3600,
            }
        ),
        order_number="O1",
        request_id="r1",
    )
    assert payment == Payment("https://pay.example/x", timedelta(seconds=3600), "O1", "r1")


def _transaction_payload(**data: object) -> dict[str, object]:
    base: dict[str, object] = {
        "orderNumber": "O1",
        "transId": "T9",
        "amount": "3,162.00",
        "toPhone": "50912345678",
        "responseCode": 1,
    }
    base.update(data)
    return {"status": 0, "code": "SUCCESS", "message": "ok", "data": base}


def test_parse_transaction_response_with_formatted_amount() -> None:
    transaction = parse_transaction_response(json_response(_transaction_payload()))
    assert transaction.amount == Decimal("3162.00")
    assert transaction.payer == "50912345678"
    assert transaction.transaction_id == "T9"
    assert transaction.status is TransactionStatus.SUCCESS
    assert transaction.is_successful


def test_parse_transaction_response_with_numeric_amount() -> None:
    transaction = parse_transaction_response(json_response(_transaction_payload(amount=10.5)))
    assert transaction.amount == Decimal("10.5")


def test_unknown_response_code_maps_to_unknown() -> None:
    zero = parse_transaction_response(json_response(_transaction_payload(responseCode=0)))
    assert zero.status is TransactionStatus.UNKNOWN
    assert zero.response_code == 0
    payload = _transaction_payload()
    del payload["data"]["responseCode"]  # type: ignore[index]
    missing = parse_transaction_response(json_response(payload))
    assert missing.status is TransactionStatus.UNKNOWN
    assert missing.response_code is None
    assert not missing.is_successful


@pytest.mark.parametrize(
    ("status", "error"),
    [(1, APIError), (3, APIError), (101, TransactionNotFoundError)],
)
def test_non_zero_status_raises(status: int, error: type[APIError]) -> None:
    response = json_response({"status": status, "code": "ERR", "message": "boom"})
    with pytest.raises(error) as caught:
        parse_transaction_response(response)
    assert caught.value.message == "boom"
    assert caught.value.status == status
    assert caught.value.code == "ERR"
    assert caught.value.http_status == 200
    with pytest.raises(error):
        parse_payment_response(response, order_number="O1", request_id="r")


@pytest.mark.parametrize(
    "response",
    [
        HttpResponse(502, {}, b"<html>Bad gateway</html>"),
        HttpResponse(200, {}, b""),
        json_response([1, 2]),
        json_response({"status": 0, "code": "SUCCESS", "message": "ok"}),
        json_response({"status": "0"}),
        json_response({"status": 0, "url": "https://x", "expiredAt": "soon"}),
        json_response({"status": 0, "data": {"orderNumber": "O1", "transId": "T"}}),
        json_response(_transaction_payload(amount="abc")),
        json_response(_transaction_payload(amount="NaN")),
        json_response(_transaction_payload(transId=None)),
        json_response({"status": 0}, status=500),
        json_response({"status": 0, "url": "https://x", "expiredAt": 1e300}),
        json_response({"status": 0, "url": "https://x", "expiredAt": 10**20}),
        json_response({"status": 0, "url": "https://x", "expiredAt": -1}),
        json_response({"status": 0, "url": "https://x", "expiredAt": True}),
        HttpResponse(200, {}, b'{"status":0,"url":"https://x","expiredAt":Infinity}'),
        HttpResponse(200, {}, b'{"status":0,"url":"https://x","expiredAt":NaN}'),
        json_response({"status": 0, "url": "javascript:alert(1)", "expiredAt": 5}),
        json_response({"status": 0, "url": "/relative", "expiredAt": 5}),
        HttpResponse(200, {}, b"[" * 100000),
    ],
)
def test_malformed_responses_raise_api_error(response: HttpResponse) -> None:
    with pytest.raises(APIError) as payment_error:
        parse_payment_response(response, order_number="O1", request_id="r")
    assert payment_error.value.http_status == response.status
    with pytest.raises(APIError) as transaction_error:
        parse_transaction_response(response)
    assert transaction_error.value.http_status == response.status


def test_http_error_with_json_envelope_keeps_it() -> None:
    response = json_response({"status": 3, "code": "INVALID", "message": "bad"}, status=400)
    with pytest.raises(APIError) as caught:
        parse_transaction_response(response)
    assert caught.value.status == 3
    assert caught.value.code == "INVALID"
    assert caught.value.message == "bad"
    assert caught.value.http_status == 400


def test_http_error_message_never_leaks_the_body() -> None:
    with pytest.raises(APIError) as caught:
        parse_transaction_response(HttpResponse(500, {}, b"password=s3cr3t"))
    assert "s3cr3t" not in str(caught.value)


def _params(case: dict[str, Any]) -> dict[str, str]:
    return {
        "orderNumber": case["order_number"],
        "code": str(case["code"]),
        "signature": case["signature"],
    }


@pytest.mark.parametrize("case", VECTORS["callbacks"], ids=lambda c: str(c["code"]))
def test_parse_callback_accepts_a_valid_signature(case: dict[str, Any]) -> None:
    callback = parse_callback(CONFIG, _params(case))
    assert callback == Callback(
        case["order_number"], case["code"], TransactionStatus.from_code(case["code"])
    )
    assert verify_callback(CONFIG, case["order_number"], case["code"], case["signature"])


def test_parse_callback_accepts_single_item_sequences() -> None:
    case = VECTORS["callbacks"][0]
    params = {key: [value] for key, value in _params(case).items()}
    assert parse_callback(CONFIG, params).order_number == case["order_number"]


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"orderNumber": "O1", "code": "1"},
        {"orderNumber": "O1", "code": "abc", "signature": "x"},
        {"orderNumber": "O1", "code": "01", "signature": "x"},
        {"orderNumber": "O1", "code": "9" * 5000, "signature": "x"},
        {"orderNumber": "O1", "code": "\u0661", "signature": "x"},
        {"orderNumber": ["O1", "O2"], "code": "1", "signature": "x"},
        {"orderNumber": [], "code": "1", "signature": "x"},
        {"orderNumber": "O1", "code": "1", "signature": "0" * 64},
    ],
)
def test_parse_callback_rejects_bad_input(params: dict[str, Any]) -> None:
    with pytest.raises(InvalidSignatureError):
        parse_callback(CONFIG, params)


def test_parse_callback_error_never_contains_signature() -> None:
    with pytest.raises(InvalidSignatureError) as caught:
        parse_callback(CONFIG, {"orderNumber": "O1", "code": "1", "signature": "deadbeef"})
    assert "deadbeef" not in str(caught.value)


def test_unlisted_integer_code_with_valid_signature_is_unknown() -> None:
    signature = callback_signature(CONFIG, order_number="O1", code=7)
    callback = parse_callback(CONFIG, {"orderNumber": "O1", "code": "7", "signature": signature})
    assert callback == Callback("O1", 7, TransactionStatus.UNKNOWN)


def test_callback_signature_case_insensitive() -> None:
    case = VECTORS["callbacks"][0]
    upper = case["signature"].upper()
    assert verify_callback(CONFIG, case["order_number"], case["code"], upper)
    params = _params(case) | {"signature": f" {upper} "}
    assert parse_callback(CONFIG, params).is_successful


@pytest.mark.parametrize("raw", ["9" * 5000, "\u0661", "abc", "", 10**12, 1.5, True, None])
def test_unparseable_response_code_maps_to_unknown(raw: object) -> None:
    transaction = parse_transaction_response(json_response(_transaction_payload(responseCode=raw)))
    assert transaction.status is TransactionStatus.UNKNOWN
    assert transaction.response_code is None
    assert not transaction.is_successful


def test_string_response_code_is_parsed() -> None:
    transaction = parse_transaction_response(json_response(_transaction_payload(responseCode="1")))
    assert transaction.status is TransactionStatus.SUCCESS
    assert transaction.response_code == 1
