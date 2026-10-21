# natcashify

A typed Python SDK for the NatCash payment gateway: create a checkout session, verify the signed
callback, retrieve a transaction. This facade re-exports `natcashify-core`.

```bash
pip install natcashify
pip install "natcashify[django]"    # or [fastapi], [flask]
```

```python
from decimal import Decimal

from natcashify import MerchantConfig, NatcashClient

with NatcashClient(MerchantConfig.from_env()) as client:
    payment = client.create_payment("ORDER-001", Decimal("250"))
    print(payment.checkout_url)
```

The default environment is the sandbox. Documentation: <https://midsonlajeanty.github.io/natcashify/>
