# From moncashify

Natcashify is inspired by [moncashify](https://pypi.org/project/moncashify/) by Lub Lorry
Lamysère, the MonCash SDK for Python: a small API that is easy to install. The two target
different gateways (MonCash and NatCash), so this page maps the concepts, not a drop-in swap.

What changes: Python 3.12+ only, typed results instead of raw dicts, one exception per kind of
failure instead of `TokenError('101', ...)`, `logging` instead of `print`, and the sandbox as the
default environment.

| moncashify | natcashify |
|---|---|
| `moncashify.API(client_id, secret_key, debug=True)` | `NatcashClient(config, sandbox=True)` with a `MerchantConfig` |
| `debug=True` (sandbox) | `sandbox=True`, the default |
| `debug=False` (live) | `sandbox=False` |
| `client_id`, `secret_key` | `MerchantConfig(private_key, partner_code, function_code, username, password, callback_url)` |
| `payment(order_id, amount)` | `create_payment(order_number, amount)` |
| `payment.redirect_url` | `payment.checkout_url` |
| token expiry in `token_details` | `payment.expires_in` (a `timedelta`) |
| `transaction_details(order_id=...)` | `get_transaction(order_number)` |
| `transaction_details(transaction_id=...)` | not available, NatCash looks transactions up by order number |
| `CredentialError`, `TokenError`, `QueryError` | `ConfigurationError`, `TransportError`, `APIError` |
| `TransactionNotFoundError`, `OrderNotFoundError` | `TransactionNotFoundError` |
| `transfer(...)` | not supported (non-goal) |

Differences to keep in mind:

- NatCash signs every request. There is no token step: the SDK computes the signatures from your
  keys.
- NatCash calls your `callback_url` with a signed query string. Verify it with `parse_callback`,
  then confirm with `get_transaction` before fulfilling, see [Callbacks](callbacks.md).
- Amounts are `Decimal` or `int` with at most 2 decimals, and are rejected rather than rounded.
  Convert a moncashify float with `Decimal(str(amount))`: `Decimal(10.1)` keeps the binary error
  of the float and is rejected.
- The async client has the same surface as the sync one.

Before:

```python
import moncashify

moncash = moncashify.API(client_id, secret_key, debug=True)
payment = moncash.payment(order_id, amount)
url = payment.redirect_url
details = moncash.transaction_details(order_id=order_id)
```

After:

```python
from decimal import Decimal

from natcashify import NatcashClient

with NatcashClient.from_env() as client:
    payment = client.create_payment(order_number, Decimal(str(amount)))
    url = payment.checkout_url
    transaction = client.get_transaction(order_number)
```
