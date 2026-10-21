import os
from decimal import Decimal
from uuid import uuid4

import pytest

from natcashify import APIError, NatcashClient, Transaction

PREFIX = "NATCASH_SANDBOX_"

pytestmark = pytest.mark.skipif(
    f"{PREFIX}PRIVATE_KEY" not in os.environ,
    reason=f"{PREFIX}* environment variables are not set",
)


def test_sandbox_round_trip() -> None:
    order_number = f"natcashify-{uuid4().hex[:12]}"
    with NatcashClient.from_env(prefix=PREFIX) as client:
        payment = client.create_payment(order_number, Decimal("1"))
        assert payment.checkout_url.startswith("https://")
        assert payment.expires_in.total_seconds() > 0
        try:
            transaction = client.get_transaction(order_number)
        except APIError:
            return
        assert isinstance(transaction, Transaction)
