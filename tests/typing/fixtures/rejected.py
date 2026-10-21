from decimal import Decimal

from natcashify import (
    AsyncNatcashClient,
    Language,
    MerchantConfig,
    NatcashClient,
    Payment,
    Transaction,
    UrllibTransport,
)

CONFIG = MerchantConfig(
    private_key="key",
    partner_code="partner",
    function_code="function",
    username="user",
    password="secret",
    callback_url="https://shop.example/natcash/callback",
)
client = NatcashClient(CONFIG)
payment: Payment = client.create_payment("O1", Decimal(1))
transaction: Transaction = client.get_transaction("O1")

client.create_payment("O1", 10.5)  # expect-error
NatcashClient(CONFIG, False)  # expect-error
client.create_payment("O1", Decimal(1), "50912345678")  # expect-error
MerchantConfig("k", "p", "f", "u", "s", "https://x.example", language="es")  # expect-error
payment.checkout_url = "https://elsewhere.example"  # expect-error
transaction.status = 1  # expect-error
client.get_transaction(1)  # expect-error
AsyncNatcashClient(CONFIG, transport=UrllibTransport())  # expect-error
Language.ES  # expect-error
client.verify_callback("O1", "1", "signature")  # expect-error
NatcashClient(CONFIG, timeout="10")  # expect-error


async def misuse() -> None:
    await NatcashClient(CONFIG).create_payment("O1", Decimal(1))  # expect-error
    AsyncNatcashClient(CONFIG).create_payment("O1", Decimal(1)).checkout_url  # expect-error
