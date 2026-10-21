import natcashify.core


def test_public_api_exports() -> None:
    assert set(natcashify.core.__all__) == {
        "DEFAULT_TIMEOUT",
        "LIVE_URL",
        "SANDBOX_URL",
        "APIError",
        "AsyncHttpTransport",
        "AsyncNatcashClient",
        "AsyncUrllibTransport",
        "Callback",
        "ConfigurationError",
        "HttpRequest",
        "HttpResponse",
        "HttpTransport",
        "InvalidPaymentError",
        "InvalidSignatureError",
        "Language",
        "MerchantConfig",
        "NatcashClient",
        "NatcashError",
        "Payment",
        "Transaction",
        "TransactionNotFoundError",
        "TransactionStatus",
        "TransportError",
        "UrllibTransport",
    }


def test_every_exported_name_resolves() -> None:
    assert all(hasattr(natcashify.core, name) for name in natcashify.core.__all__)


def test_testing_stays_a_submodule() -> None:
    assert "FakeTransport" not in dir(natcashify.core)
