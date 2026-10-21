from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from enum import IntEnum


class TransactionStatus(IntEnum):
    SUCCESS = 1
    FAILED = -1
    UNKNOWN = -3

    @classmethod
    def from_code(cls, code: int | None) -> "TransactionStatus":
        try:
            return cls(code)
        except ValueError:
            return TransactionStatus.UNKNOWN


@dataclass(frozen=True, slots=True)
class Payment:
    checkout_url: str
    expires_in: timedelta
    order_number: str
    request_id: str


@dataclass(frozen=True, slots=True)
class Transaction:
    order_number: str
    transaction_id: str
    amount: Decimal
    payer: str
    status: TransactionStatus
    response_code: int | None

    @property
    def is_successful(self) -> bool:
        return self.status is TransactionStatus.SUCCESS


@dataclass(frozen=True, slots=True)
class Callback:
    order_number: str
    code: int
    status: TransactionStatus

    @property
    def is_successful(self) -> bool:
        return self.status is TransactionStatus.SUCCESS
