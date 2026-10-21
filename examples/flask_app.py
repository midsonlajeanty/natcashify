from decimal import Decimal

from flask import Flask
from flask.typing import ResponseReturnValue

from natcashify import Callback, MerchantConfig
from natcashify.core.testing import FakeTransport, json_response, sign_callback
from natcashify.flask import Natcash

ORDERS = {"ORDER-001": Decimal("250")}
CONFIG = {
    "NATCASH_PRIVATE_KEY": "private-key",
    "NATCASH_PARTNER_CODE": "PARTNER",
    "NATCASH_FUNCTION_CODE": "function-code",
    "NATCASH_USERNAME": "merchant",
    "NATCASH_PASSWORD": "secret",
    "NATCASH_CALLBACK_URL": "https://shop.example/natcash/callback",
}
TRANSPORT = FakeTransport(
    json_response(
        {
            "status": 0,
            "code": "0",
            "message": "Success",
            "data": {
                "orderNumber": "ORDER-001",
                "transId": "T-1",
                "amount": 250,
                "toPhone": "50912345678",
                "responseCode": 1,
            },
        }
    )
)

app = Flask(__name__)
app.config.from_mapping(CONFIG)
natcash = Natcash(app, transport=TRANSPORT)


@app.get("/natcash/callback")
@natcash.callback
def callback(callback: Callback) -> ResponseReturnValue:
    transaction = natcash.client.get_transaction(callback.order_number)
    paid = transaction.is_successful and transaction.amount == ORDERS[callback.order_number]
    return {"order": callback.order_number, "status": "paid" if paid else "not paid"}


if __name__ == "__main__":
    config = MerchantConfig.from_env(environ=CONFIG)
    signature = sign_callback(config, "ORDER-001", 1)
    query = {"orderNumber": "ORDER-001", "code": "1", "signature": signature}
    print(app.test_client().get("/natcash/callback", query_string=query).get_json())
