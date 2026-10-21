# Transactions

```python
transaction = client.get_transaction("ORDER-001")
```

`get_transaction(order_number, *, request_id=None) -> Transaction` (awaited on the async client).
`request_id` defaults to a fresh UUIDv7.

`Transaction` is frozen:

| Field | Type | Meaning |
|---|---|---|
| `order_number` | `str` | The order number |
| `transaction_id` | `str` | NatCash transaction id (`transId`) |
| `amount` | `Decimal` | Amount charged. Thousands separators such as `"3,162.00"` are parsed |
| `payer` | `str` | Payer phone number (`toPhone`), empty when absent |
| `status` | `TransactionStatus` | See below |
| `response_code` | `int \| None` | The raw `responseCode` |
| `is_successful` | `bool` | Property, `status is TransactionStatus.SUCCESS` |

## Status

`TransactionStatus` is an `IntEnum`:

| Member | Value |
|---|---|
| `SUCCESS` | `1` |
| `FAILED` | `-1` |
| `UNKNOWN` | `-3` |

Any `responseCode` outside these values, or a missing one, maps to `TransactionStatus.UNKNOWN`
instead of raising, and `response_code` keeps the raw integer. A pending order therefore never
crashes the lookup that follows a callback. Only `1` is ever successful.

## Order number check

If the gateway answers with a transaction for a different order number than the one you asked
for, `get_transaction` raises `APIError` rather than returning it.

## Not found

An unknown order raises `TransactionNotFoundError` (envelope status `101`), a subclass of
`APIError`. See [Errors](errors.md).
