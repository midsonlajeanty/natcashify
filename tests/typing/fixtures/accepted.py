import asyncio
from datetime import timedelta
from decimal import Decimal

from natcashify import (
    AsyncNatcashClient,
    Callback,
    Language,
    MerchantConfig,
    NatcashClient,
    Payment,
    Transaction,
    TransactionStatus,
)

CONFIG = MerchantConfig(
    private_key="key",
    partner_code="partner",
    function_code="function",
    username="user",
    password="secret",
    callback_url="https://shop.example/natcash/callback",
    payer_pays_fee=True,
    language=Language.HT,
)


def sync_flow() -> None:
    with NatcashClient(CONFIG, sandbox=True) as client:
        payment: Payment = client.create_payment("ORDER-001", Decimal("250"), phone_number="50912345678")
        url: str = payment.checkout_url
        expires: timedelta = payment.expires_in
        transaction: Transaction = client.get_transaction("ORDER-001")
        status: TransactionStatus = transaction.status
        successful: bool = transaction.is_successful
        valid: bool = client.verify_callback("ORDER-001", 1, "signature")
        callback: Callback = client.parse_callback({"orderNumber": "ORDER-001"})
        print(url, expires, status, successful, valid, callback)


async def async_flow() -> None:
    async with AsyncNatcashClient(CONFIG, sandbox=False) as client:
        payment = await client.create_payment("ORDER-002", 100, skip_phone_input=False)
        transaction = await client.get_transaction("ORDER-002", request_id="request")
        print(payment.checkout_url, transaction.status.name)


asyncio.run(async_flow())
sync_flow()
