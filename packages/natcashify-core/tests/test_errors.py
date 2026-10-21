from natcashify.core.errors import (
    APIError,
    ConfigurationError,
    InvalidPaymentError,
    InvalidSignatureError,
    NatcashError,
    TransactionNotFoundError,
    TransportError,
)


def test_api_error_carries_the_envelope() -> None:
    error = APIError("Merchant not found", status=100, code="MERCHANT_NOT_FOUND", http_status=200)
    assert (error.status, error.code, error.http_status, str(error)) == (
        100,
        "MERCHANT_NOT_FOUND",
        200,
        "Merchant not found",
    )
    assert error.message == "Merchant not found"


def test_api_error_envelope_is_optional() -> None:
    error = APIError("boom")
    assert (error.status, error.code, error.http_status) == (None, None, None)


def test_transaction_not_found_is_an_api_error() -> None:
    assert issubclass(TransactionNotFoundError, APIError)


def test_every_error_derives_from_natcash_error() -> None:
    for error in (
        ConfigurationError,
        InvalidPaymentError,
        InvalidSignatureError,
        TransportError,
        APIError,
    ):
        assert issubclass(error, NatcashError)
