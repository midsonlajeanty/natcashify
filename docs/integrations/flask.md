# Flask

```bash
pip install "natcashify[flask]"
```

Flask 3.0 or newer. The extension is sync only.

## Configuration

`Natcash(app)` builds a `NatcashClient` from `app.config`, using the `NATCASH_*` keys (see
[Getting started](../getting-started.md#from-the-environment)). The sandbox is the default.

```python
from decimal import Decimal

from flask import Flask, redirect
from natcashify.core import Callback
from natcashify.flask import Natcash

app = Flask(__name__)
app.config.update(
    NATCASH_PRIVATE_KEY="...",
    NATCASH_PARTNER_CODE="...",
    NATCASH_FUNCTION_CODE="...",
    NATCASH_USERNAME="...",
    NATCASH_PASSWORD="...",
    NATCASH_CALLBACK_URL="https://shop.example/natcash/callback",
)
natcash = Natcash(app)


@app.post("/checkout")
def checkout():
    payment = natcash.client.create_payment("ORDER-001", Decimal("250"))
    return redirect(payment.checkout_url)


@app.get("/natcash/callback")
@natcash.callback
def callback(callback: Callback):
    transaction = natcash.client.get_transaction(callback.order_number)
    order = orders[callback.order_number]
    if transaction.is_successful and transaction.amount == order.amount:
        return "paid"
    return "not paid"
```

`natcash.client` returns the client of the current app and needs an application context.

The `callback` decorator verifies the signature, aborts with `400` when it is invalid and passes
the `Callback` as the first argument. It never calls `get_transaction` itself: the callback
reaches your shop through the payer's browser, so confirm with the gateway and compare the amount
before fulfilling, see [Callbacks](../callbacks.md).

## Application factory

```python
import os

natcash = Natcash()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update({k: v for k, v in os.environ.items() if k.startswith("NATCASH_")})
    natcash.init_app(app)
    return app
```

## Testing

Pass a transport: `Natcash(app, transport=FakeTransport(...))`, and sign test callbacks with
`sign_callback`, see [Getting started](../getting-started.md#testing-your-own-code).
