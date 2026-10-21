# Callbacks

After the payer completes (or abandons) the checkout, NatCash redirects their browser to your
`callback_url` with three query parameters:

| Parameter | Meaning |
|---|---|
| `orderNumber` | The order number |
| `code` | `1` success, `-1` failed, `-3` unknown |
| `signature` | HMAC-SHA256 signed with your `function_code` |

## Verify and parse

```python
callback = client.parse_callback(request_query_params)
```

`parse_callback(params) -> Callback` reads the three parameters from a mapping of strings (or of
lists of strings, as Django and Starlette expose them) and raises `InvalidSignatureError` when:

- a parameter is missing or repeated,
- `code` is not a canonical integer (`"1"` and `"-1"` pass, `"01"`, `"+1"` and `"1.0"` do not),
- the signature does not match. The comparison is constant time.

`Callback` is frozen: `order_number`, `code` (the raw integer), `status` (a
[`TransactionStatus`](transactions.md#status)) and the `is_successful` property.

`verify_callback(order_number, code, signature) -> bool` is the lower-level check. Both are plain
methods, also on `AsyncNatcashClient`, and do no I/O.

## Do not trust the callback alone

The callback reaches your shop through the payer's browser. A valid signature proves it was
produced by NatCash for that order, but you should still confirm the outcome with the gateway
before fulfilling the order:

1. Verify the callback.
2. Look the order up. An unknown order number gets no fulfillment.
3. Stop if the order is already paid: the payer's browser replays the callback on every refresh,
   so fulfillment must run once.
4. Call `get_transaction(callback.order_number)`.
5. Fulfill only when `transaction.is_successful` and `transaction.amount` equals the amount of
   your order.

Make `mark_paid` itself idempotent too (a conditional update such as
`UPDATE orders SET paid = true WHERE id = ? AND NOT paid`), since two replays can arrive at once.

```python
from natcashify import InvalidSignatureError, NatcashError


def handle_callback(params: dict[str, str]) -> str:
    try:
        callback = client.parse_callback(params)
    except InvalidSignatureError:
        return "invalid"
    order = orders.get(callback.order_number)
    if order is None:
        return "unknown order"
    if order.is_paid:
        return "paid"
    try:
        transaction = client.get_transaction(callback.order_number)
    except NatcashError:
        return "retry later"
    if transaction.is_successful and transaction.amount == order.amount:
        order.mark_paid(transaction.transaction_id)
        return "paid"
    return "not paid"
```

The adapters verify the signature for you and hand your view a `Callback`, see the
[Django](integrations/django.md), [FastAPI](integrations/fastapi.md) and
[Flask](integrations/flask.md) pages. They never call `get_transaction` on their own.
