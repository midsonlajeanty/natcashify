# FastAPI

```bash
pip install "natcashify[fastapi]"
```

FastAPI 0.115 or newer.

## Configuration

The dependencies build the client with `from_env()`, so set the `NATCASH_*` environment variables
(see [Getting started](../getting-started.md#from-the-environment)). The sandbox is the default.

## Dependencies

- `get_natcash_client` returns a cached `NatcashClient`.
- `get_async_natcash_client` returns a cached `AsyncNatcashClient`.
- `NatcashCallback` is an `Annotated` dependency that parses and verifies the callback query
  string and returns a `Callback`. It answers `400` on a bad signature.

```python
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI
from natcashify import AsyncNatcashClient
from natcashify.fastapi import NatcashCallback, get_async_natcash_client

app = FastAPI()
Client = Annotated[AsyncNatcashClient, Depends(get_async_natcash_client)]


@app.post("/checkout")
async def checkout(client: Client) -> dict[str, str]:
    payment = await client.create_payment("ORDER-001", Decimal("250"))
    return {"url": payment.checkout_url}


@app.get("/natcash/callback")
async def callback(callback: NatcashCallback, client: Client) -> dict[str, str]:
    transaction = await client.get_transaction(callback.order_number)
    order = orders[callback.order_number]
    if transaction.is_successful and transaction.amount == order.amount:
        return {"status": "paid"}
    return {"status": "not paid"}
```

The dependency never calls `get_transaction` itself: the callback reaches your shop through the
payer's browser, so confirm with the gateway and compare the amount before fulfilling, see
[Callbacks](../callbacks.md).

## Testing

Override the dependency with a client that uses a fake transport:

```python
from natcashify.core.testing import AsyncFakeTransport

app.dependency_overrides[get_async_natcash_client] = lambda: AsyncNatcashClient.from_env(
    environ=ENV, transport=AsyncFakeTransport()
)
```

Sign test callbacks with `sign_callback`, see
[Getting started](../getting-started.md#testing-your-own-code).
