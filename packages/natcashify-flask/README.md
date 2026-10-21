# natcashify-flask

Flask extension for Natcashify, configured from `NATCASH_*` keys in `app.config`.

```bash
pip install natcashify-flask
```

```python
from natcashify.core import Callback
from natcashify.flask import Natcash

natcash = Natcash(app)


@app.get("/natcash/callback")
@natcash.callback
def callback(callback: Callback):
    transaction = natcash.client.get_transaction(callback.order_number)
    ...
```

The decorator aborts with 400 on an invalid signature. Confirm the transaction before fulfilling,
and skip an unknown or already paid order: the browser replays the callback on refresh.
Documentation: <https://midsonlajeanty.github.io/natcashify/integrations/flask/>
