# natcashify-fastapi

FastAPI integration for Natcashify: client dependencies and a verified callback dependency.

```bash
pip install natcashify-fastapi
```

```python
from natcashify.fastapi import NatcashCallback, get_async_natcash_client


@app.get("/natcash/callback")
async def callback(callback: NatcashCallback, client: Client) -> dict[str, str]:
    transaction = await client.get_transaction(callback.order_number)
    ...
```

`NatcashCallback` answers 400 on an invalid signature. Confirm the transaction before fulfilling.
The clients are built from the `NATCASH_*` environment variables.
Documentation: <https://midsonlajeanty.github.io/natcashify/integrations/fastapi/>
