# Natcashify

**A typed Python SDK for the NatCash payment gateway.**

Natcashify creates a NatCash checkout session, verifies the signed callback NatCash sends back
through the payer's browser, and retrieves a transaction by order number. It has a sync and an
async client with the same surface, is checked by Pyright in strict mode, and its core uses only
the standard library.

It is inspired by [moncashify](https://pypi.org/project/moncashify/) by Lub Lorry Lamysère, the
MonCash SDK that made payment integration in Haiti a matter of a few lines. If you come from it,
read [From moncashify](moncashify.md).

```python
from decimal import Decimal

from natcashify import MerchantConfig, NatcashClient

config = MerchantConfig.from_env()
with NatcashClient(config) as client:
    payment = client.create_payment("ORDER-001", Decimal("250"))
    print(payment.checkout_url)
```

The default environment is the **sandbox**. Nothing moves real money until you pass
`sandbox=False` (or set `NATCASH_SANDBOX=false`).

## Packages

| Package | Contents |
|---|---|
| `natcashify` | Facade re-exporting the core, with the `django`, `fastapi` and `flask` extras |
| `natcashify-core` | Configuration, signing, sync and async clients, transports, testing fakes. Standard library only. |
| `natcashify-django` | Settings, cached clients, system check and callback view decorator |
| `natcashify-fastapi` | Client dependencies and the `NatcashCallback` dependency |
| `natcashify-flask` | `Natcash` extension and callback decorator |

```bash
pip install natcashify              # the core
pip install "natcashify[django]"    # or [fastapi], [flask]
```

Next: [Getting started](getting-started.md).
