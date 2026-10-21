# natcashify-core

Framework-agnostic core of Natcashify: configuration, signing, sync and async gateway clients,
HTTP transports and testing fakes. Standard library only.

```bash
pip install natcashify-core
```

```python
from decimal import Decimal

from natcashify.core import MerchantConfig, NatcashClient

with NatcashClient(MerchantConfig.from_env()) as client:
    payment = client.create_payment("ORDER-001", Decimal("250"))
    print(payment.checkout_url)
```

`natcashify.core.testing` provides `FakeTransport` and `AsyncFakeTransport` for tests without a
network. Documentation: <https://midsonlajeanty.github.io/natcashify/>
