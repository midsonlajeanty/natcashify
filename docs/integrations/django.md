# Django

```bash
pip install "natcashify[django]"
```

Django 4.2 or newer.

## Settings

```python
INSTALLED_APPS = [
    # ...
    "natcashify.django",
]

NATCASH = {
    "PRIVATE_KEY": env("NATCASH_PRIVATE_KEY"),
    "PARTNER_CODE": env("NATCASH_PARTNER_CODE"),
    "FUNCTION_CODE": env("NATCASH_FUNCTION_CODE"),
    "USERNAME": env("NATCASH_USERNAME"),
    "PASSWORD": env("NATCASH_PASSWORD"),
    "CALLBACK_URL": "https://shop.example/natcash/callback/",
    # optional
    "ENABLE_FEE": True,
    "LANGUAGE": "ht",
    "SANDBOX": True,
    "TIMEOUT": 10,
}
```

The keys are the `from_env` names without the `NATCASH_` prefix, plus `SANDBOX` (default `True`)
and `TIMEOUT` (default `10` seconds). A Django system check (`natcashify.E001`) reports a missing
or invalid `NATCASH` setting when you run `manage.py check`.

## Clients

`get_client()` returns a `NatcashClient` and `get_async_client()` an `AsyncNatcashClient`, each
cached per process and reset when the `NATCASH` setting changes (for example under
`override_settings`).

```python
from decimal import Decimal

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from natcashify.django import get_client


def checkout(request: HttpRequest) -> HttpResponse:
    payment = get_client().create_payment("ORDER-001", Decimal("250"))
    return HttpResponseRedirect(payment.checkout_url)
```

## Callback view

`natcash_callback` verifies the signature and passes a `Callback` as the second argument. It
returns `400` on an invalid signature. It works on sync and async views.

```python
from django.http import Http404, HttpRequest, HttpResponse
from natcashify.core import Callback
from natcashify.django import get_client, natcash_callback


@natcash_callback
def callback(request: HttpRequest, callback: Callback) -> HttpResponse:
    order = Order.objects.filter(number=callback.order_number).first()
    if order is None:
        raise Http404
    if order.is_paid:
        return HttpResponse("paid")
    transaction = get_client().get_transaction(callback.order_number)
    if transaction.is_successful and transaction.amount == order.amount:
        order.mark_paid(transaction.transaction_id)
        return HttpResponse("paid")
    return HttpResponse("not paid")
```

The decorator never calls `get_transaction` itself: the callback reaches your shop through the
payer's browser, so confirm with the gateway and compare the amount before fulfilling. The
browser replays the callback on refresh, so skip orders that are already paid, see
[Callbacks](../callbacks.md).

An async view uses `get_async_client()` and `await`:

```python
@natcash_callback
async def callback(request: HttpRequest, callback: Callback) -> HttpResponse:
    transaction = await get_async_client().get_transaction(callback.order_number)
    ...
```
