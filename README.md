# Natcashify

A typed Python SDK for the [NatCash](https://natcom.com.ht) payment gateway (Natcom, Haiti).
Create a checkout session, verify the signed callback, retrieve a transaction. Sync and async
clients with the same surface, a standard-library-only core, and thin Django, FastAPI and Flask
adapters.

Inspired by [moncashify](https://pypi.org/project/moncashify/) by Lub Lorry Lamysère, and wire
compatible with the author's PHP SDK.

```bash
pip install natcashify              # the core
pip install "natcashify[django]"    # or [fastapi], [flask]
```

Python 3.12 or newer. The default environment is the **sandbox**.

## Quickstart

```python
from decimal import Decimal

from natcashify import MerchantConfig, NatcashClient

config = MerchantConfig.from_env()  # NATCASH_PRIVATE_KEY, NATCASH_PARTNER_CODE, ...

with NatcashClient(config) as client:
    payment = client.create_payment("ORDER-001", Decimal("250"), phone_number="50912345678")
    print(payment.checkout_url)  # send the payer here
```

NatCash then redirects the payer to your `callback_url`. Verify it, confirm the transaction with
the gateway, and fulfill only when it succeeded and the amount matches your order:

```python
callback = client.parse_callback(request_query_params)  # InvalidSignatureError if forged
order = orders.get(callback.order_number)
if order is not None and not order.is_paid:
    transaction = client.get_transaction(callback.order_number)
    if transaction.is_successful and transaction.amount == order.amount:
        order.mark_paid(transaction.transaction_id)
```

The callback reaches your shop through the payer's browser, which is why the transaction lookup
comes before fulfilling, and the browser replays it on refresh, which is why an order already
paid is skipped.

## Rules worth knowing

- Amounts are `Decimal` or `int`, strictly positive, at most 2 decimals and at most
  `999999999.99`. They are rejected, never rounded.
- `phone_number` must match `^509\d{8}$`.
- An unknown response code maps to `TransactionStatus.UNKNOWN` instead of raising.
- Every failure derives from `NatcashError`: `ConfigurationError`, `InvalidPaymentError`,
  `InvalidSignatureError`, `TransportError`, `APIError` (and `TransactionNotFoundError`).
- `natcashify.core.testing` ships `FakeTransport`, `AsyncFakeTransport` and `sign_callback` for
  your own tests.

## Documentation

<https://midsonlajeanty.github.io/natcashify/>: getting started, payments, callbacks,
transactions, errors, custom transports, a migration page for moncashify users, and one page per
adapter.

## Packages

| Package | Contents |
|---|---|
| `natcashify` | Facade re-exporting the core |
| `natcashify-core` | Standard library only |
| `natcashify-django` | Settings, system check, callback view decorator |
| `natcashify-fastapi` | Dependencies and `NatcashCallback` |
| `natcashify-flask` | `Natcash` extension |

## License

MIT
