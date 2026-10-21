from datetime import timedelta
from decimal import Decimal

import pytest

from natcashify.core.models import Callback, Payment, Transaction, TransactionStatus


@pytest.mark.parametrize(
    ("code", "status"),
    [
        (1, TransactionStatus.SUCCESS),
        (-1, TransactionStatus.FAILED),
        (-3, TransactionStatus.UNKNOWN),
        (0, TransactionStatus.UNKNOWN),
        (42, TransactionStatus.UNKNOWN),
        (None, TransactionStatus.UNKNOWN),
    ],
)
def test_from_code(code: int | None, status: TransactionStatus) -> None:
    assert TransactionStatus.from_code(code) is status


def test_only_success_is_successful() -> None:
    def transaction(status: TransactionStatus) -> Transaction:
        return Transaction("O1", "T1", Decimal("1"), "509", status, int(status))

    assert transaction(TransactionStatus.SUCCESS).is_successful
    assert not transaction(TransactionStatus.FAILED).is_successful
    assert not transaction(TransactionStatus.UNKNOWN).is_successful
    assert Callback("O1", 1, TransactionStatus.SUCCESS).is_successful
    assert not Callback("O1", 7, TransactionStatus.UNKNOWN).is_successful


def test_payment_is_frozen() -> None:
    payment = Payment("https://x", timedelta(seconds=1), "O1", "r1")
    with pytest.raises(AttributeError):
        payment.order_number = "O2"  # type: ignore[misc]
