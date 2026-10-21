# Errors

Every error raised by Natcashify derives from `NatcashError`.

```text
NatcashError
├── ConfigurationError
├── InvalidPaymentError
├── InvalidSignatureError
├── TransportError
└── APIError
    └── TransactionNotFoundError
```

| Error | Raised when |
|---|---|
| `ConfigurationError` | A credential is empty, `callback_url` is not absolute http(s), an environment variable is missing or invalid, or `timeout` is not a finite number greater than zero |
| `InvalidPaymentError` | `create_payment` arguments break the [rules](payments.md#rules). Raised before any I/O |
| `InvalidSignatureError` | A callback has a bad or missing signature, a missing or repeated parameter, or a non-canonical `code` |
| `TransportError` | Network failure or timeout. The cause is chained |
| `APIError` | The gateway answered with a non-zero envelope status, a non-2xx HTTP status, or a malformed body |
| `TransactionNotFoundError` | Envelope status `101` |

## APIError

`APIError` carries `message`, `status` (envelope status), `code` (envelope code) and
`http_status`. Any of the last three may be `None`.

- A non-zero envelope `status` raises `APIError` with the envelope fields.
- A non-2xx HTTP response raises `APIError` with the envelope when the body is JSON, otherwise
  with `http_status` only.
- A malformed success body raises `APIError`, never `KeyError`.

Envelope statuses: `1` common error, `2` transaction expired, `3` invalid parameters, `4`
missing parameters, `100` merchant not found, `101` transaction not found, `102` duplicate
request id.

Messages never contain credentials or signatures.

```python
from natcashify import APIError, TransactionNotFoundError, TransportError

try:
    transaction = client.get_transaction("ORDER-001")
except TransactionNotFoundError:
    ...
except APIError as error:
    log.warning("gateway said %s (%s)", error.message, error.status)
except TransportError:
    ...
```
