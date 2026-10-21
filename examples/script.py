from decimal import Decimal

from natcashify import MerchantConfig, NatcashClient
from natcashify.core.signing import callback_signature
from natcashify.core.testing import FakeTransport, json_response

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
            "url": "https://testmerchantpay.natcom.com.ht/checkout/abc",
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
                "amount": "250.00",
                "toPhone": "50912345678",
                "responseCode": 1,
            },
        }
    ),
)

with NatcashClient(config, transport=transport) as client:
    payment = client.create_payment("ORDER-001", Decimal("250"), phone_number="50912345678")
    print("redirect the payer to", payment.checkout_url)

    query = {
        "orderNumber": "ORDER-001",
        "code": "1",
        "signature": callback_signature(config, order_number="ORDER-001", code=1),
    }
    callback = client.parse_callback(query)
    transaction = client.get_transaction(callback.order_number)
    paid = transaction.is_successful and transaction.amount == Decimal("250")
    print(f"order={transaction.order_number} paid={paid}")
