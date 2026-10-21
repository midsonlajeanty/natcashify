# Payments

```python
payment = client.create_payment(
    "ORDER-001",
    Decimal("250"),
    phone_number="50912345678",
    skip_phone_input=False,
)
```

`create_payment(order_number, amount, *, phone_number=None, skip_phone_input=False) -> Payment`
(awaited on `AsyncNatcashClient`).

`Payment` is frozen and has:

| Field | Type | Meaning |
|---|---|---|
| `checkout_url` | `str` | Send the payer here (an absolute http(s) URL) |
| `expires_in` | `timedelta` | How long the checkout session lasts |
| `order_number` | `str` | The order number you passed |
| `request_id` | `str` | Fresh UUID4 sent with this call |

Redirect the payer to `checkout_url`. NatCash redirects them back to your `callback_url`, see
[Callbacks](callbacks.md).

## Rules

Violations raise `InvalidPaymentError` before any network I/O.

- `order_number` must not be empty. Keep it unique per order: it is the key you will look the
  transaction up with.
- `amount` is a `Decimal` or an `int`. A `float` is rejected.
- `amount` is strictly positive, has at most 2 decimal places and is at most `999999999.99`.
  Anything else is rejected, never rounded.
- `phone_number` is optional and must match `^509\d{8}$` (country code 509, then 8 digits).
- `skip_phone_input=True` requires `phone_number`.

```python
from decimal import Decimal

client.create_payment("A", Decimal("10.5"))  # ok
client.create_payment("A", 100)  # ok
client.create_payment("A", Decimal("10.555"))  # InvalidPaymentError
client.create_payment("A", 10.5)  # InvalidPaymentError (float)
client.create_payment("A", 0)  # InvalidPaymentError
```

The limits keep every accepted amount exact in the signed string, which reproduces the
representation the PHP SDK signs.

## Fees and language

`payer_pays_fee` and `language` come from the `MerchantConfig` (see
[Getting started](getting-started.md)) and apply to every payment of that client.
