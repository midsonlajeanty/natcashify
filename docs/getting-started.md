# Getting started

## Install

```bash
pip install natcashify
```

Python 3.12 or newer is required.

## Configure

`MerchantConfig` holds your merchant credentials. It validates on construction (every credential
non-empty, `callback_url` an absolute http(s) URL) and its `repr` masks `private_key` and
`password`.

```python
from natcashify import Language, MerchantConfig

config = MerchantConfig(
    private_key="...",
    partner_code="...",
    function_code="...",
    username="...",
    password="...",
    callback_url="https://shop.example/natcash/callback",
    payer_pays_fee=True,
    language=Language.HT,
)
```

`payer_pays_fee` defaults to `True` and is sent as `enableFee`. `Language` is `HT`, `FR` or `EN`
(default `HT`).

### From the environment

`MerchantConfig.from_env(prefix="NATCASH_")` and `NatcashClient.from_env(prefix="NATCASH_")` read
the same variable names as the PHP Laravel config:

| Variable | Required | Meaning |
|---|---|---|
| `NATCASH_PRIVATE_KEY` | yes | Key signing payment and transaction requests |
| `NATCASH_PARTNER_CODE` | yes | Partner code |
| `NATCASH_FUNCTION_CODE` | yes | Key verifying callbacks |
| `NATCASH_USERNAME` | yes | Merchant username |
| `NATCASH_PASSWORD` | yes | Merchant password |
| `NATCASH_CALLBACK_URL` | yes | Absolute http(s) URL NatCash redirects the payer to |
| `NATCASH_ENABLE_FEE` | no | Boolean, default `true` |
| `NATCASH_LANGUAGE` | no | `ht`, `fr` or `en`, default `ht` |
| `NATCASH_SANDBOX` | no | Boolean, default `true`. Read by `NatcashClient.from_env` only |
| `NATCASH_TIMEOUT` | no | Seconds, a number greater than zero, default `10`. Read by `NatcashClient.from_env` only |

Booleans accept `true/false`, `1/0`, `yes/no` and `on/off`. A missing required variable or an
invalid value raises `ConfigurationError`. Both methods take an `environ` mapping to read from
instead of `os.environ`.

## Create a client

```python
from natcashify import NatcashClient

client = NatcashClient(config)  # sandbox, 10 s timeout
client = NatcashClient(config, sandbox=False)  # live
client = NatcashClient(config, timeout=20.0)
```

`sandbox` and `timeout` are keyword-only. Use the client as a context manager, or call `close()`.

`AsyncNatcashClient` has the same constructor and methods, awaited, and is an async context
manager (`aclose()`):

```python
import asyncio
from decimal import Decimal

from natcashify import AsyncNatcashClient


async def main() -> None:
    async with AsyncNatcashClient(config) as client:
        payment = await client.create_payment("ORDER-001", Decimal("250"))
        print(payment.checkout_url)


asyncio.run(main())
```

## Environments

| | URL |
|---|---|
| Sandbox (default) | `https://testmerchantpay.natcom.com.ht/api/online-payment/` |
| Live | `https://merchantpay.natcom.com.ht/api/online-payment/` |

The constants `SANDBOX_URL`, `LIVE_URL` and `DEFAULT_TIMEOUT` are exported.

## Logging

Requests and responses are logged at debug level on `logging.getLogger("natcashify")`, with the
order number and request id but never credentials or signatures. A `User-Agent: natcashify/<version>`
header is sent.

## Testing your own code

`natcashify.core.testing` ships fakes so your tests never touch the network:

```python
from natcashify import MerchantConfig, NatcashClient
from natcashify.core.testing import FakeTransport, json_response

transport = FakeTransport(
    json_response(
        {
            "status": 0,
            "code": "0",
            "message": "ok",
            "url": "https://pay.example/checkout/1",
            "expiredAt": 600,
        }
    )
)
client = NatcashClient(config, transport=transport)
client.create_payment("ORDER-001", 100)
assert transport.requests[0].url.endswith("/credential")
```

`FakeTransport` and `AsyncFakeTransport` return queued `HttpResponse` objects in order, record the
`HttpRequest` objects they receive in `requests`, and raise `AssertionError` when the queue is
empty. `json_response(payload, status=200)` builds a response.

See [`examples/script.py`](https://github.com/midsonlajeanty/natcashify/blob/main/examples/script.py)
for a complete run.
