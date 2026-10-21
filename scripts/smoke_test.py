from decimal import Decimal
from importlib.resources import files

from natcashify import MerchantConfig, NatcashClient, TransactionStatus
from natcashify.core.testing import FakeTransport, json_response, sign_callback

PORTIONS = ("core", "django", "fastapi", "flask")

config = MerchantConfig(
    private_key="private-key",
    partner_code="PARTNER",
    function_code="function-code",
    username="merchant",
    password="secret",
    callback_url="https://shop.example/natcash/callback",
)
transport = FakeTransport(
    json_response(
        {
            "status": 0,
            "code": "0",
            "message": "Success",
            "url": "https://checkout.example/abc",
            "expiredAt": 900,
        }
    ),
    json_response(
        {
            "status": 0,
            "code": "0",
            "message": "Success",
            "data": {
                "orderNumber": "ORDER-001",
                "transId": "T-1",
                "amount": 250,
                "toPhone": "50912345678",
                "responseCode": 1,
            },
        }
    ),
)

with NatcashClient(config, transport=transport) as client:
    payment = client.create_payment("ORDER-001", Decimal("250"))
    assert payment.checkout_url == "https://checkout.example/abc"
    callback = client.parse_callback(
        {
            "orderNumber": "ORDER-001",
            "code": "1",
            "signature": sign_callback(config, "ORDER-001", 1),
        }
    )
    assert callback.status is TransactionStatus.SUCCESS
    transaction = client.get_transaction("ORDER-001")
    assert transaction.is_successful
    assert transaction.amount == Decimal("250")

assert files("natcashify").joinpath("py.typed").is_file()
for portion in PORTIONS:
    assert files(f"natcashify.{portion}").joinpath("py.typed").is_file(), portion
