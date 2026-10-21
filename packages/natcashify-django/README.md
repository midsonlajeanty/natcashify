# natcashify-django

Django integration for Natcashify: a `NATCASH` setting, cached clients, a system check and a
callback view decorator.

```bash
pip install natcashify-django
```

```python
INSTALLED_APPS = ["natcashify.django", ...]
NATCASH = {
    "PRIVATE_KEY": "...",
    "PARTNER_CODE": "...",
    "FUNCTION_CODE": "...",
    "USERNAME": "...",
    "PASSWORD": "...",
    "CALLBACK_URL": "https://shop.example/natcash/callback/",
}
```

```python
from natcashify.core import Callback
from natcashify.django import get_client, natcash_callback


@natcash_callback
def callback(request, callback: Callback):
    transaction = get_client().get_transaction(callback.order_number)
    ...
```

The decorator returns 400 on an invalid signature. Confirm the transaction before fulfilling.
Documentation: <https://midsonlajeanty.github.io/natcashify/integrations/django/>
