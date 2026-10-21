import os
from decimal import Decimal
from uuid import uuid4

import pytest

from natcashify import APIError, MerchantConfig, NatcashClient, Transaction

PREFIX = "NATCASH_SANDBOX_"
REQUIRED = tuple(
    f"{PREFIX}{name}"
    for name in (
        "PRIVATE_KEY",
        "PARTNER_CODE",
        "FUNCTION_CODE",
        "USERNAME",
        "PASSWORD",
        "CALLBACK_URL",
    )
)

pytestmark = pytest.mark.skipif(
    not all(os.environ.get(key, "").strip() for key in REQUIRED),
    reason=f"{PREFIX}* environment variables are not all set",
)


def test_sandbox_round_trip() -> None:
    order_number = f"natcashify-{uuid4().hex[:12]}"
    config = MerchantConfig.from_env(prefix=PREFIX)
    with NatcashClient(config, sandbox=True) as client:
        assert client.sandbox is True
        payment = client.create_payment(order_number, Decimal("1"))
        assert payment.checkout_url.startswith("https://")
        assert payment.expires_in.total_seconds() > 0
        try:
            transaction = client.get_transaction(order_number)
        except APIError:
            return
        assert isinstance(transaction, Transaction)
