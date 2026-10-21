from decimal import Decimal

from flask import Flask
from flask.typing import ResponseReturnValue

from natcashify import (
    APIError,
    Callback,
    Language,
    MerchantConfig,
    NatcashClient,
    Payment,
    Transaction,
    TransactionStatus,
)
from natcashify.core.testing import FakeTransport
from natcashify.django import natcash_callback
from natcashify.fastapi import NatcashCallback
from natcashify.flask import Natcash

config = MerchantConfig(
    private_key="k",
    partner_code="p",
    function_code="f",
    username="u",
    password="w",
    callback_url="https://shop.example/cb",
    language=Language.EN,
)
client = NatcashClient(config, sandbox=True, transport=FakeTransport())


def pay(order_number: str) -> Payment:
    return client.create_payment(order_number, Decimal("10.50"), phone_number="50912345678")


def lookup(order_number: str) -> Transaction | None:
    try:
        return client.get_transaction(order_number)
    except APIError:
        return None


def status_name(callback: Callback) -> str:
    return TransactionStatus(callback.status).name


app = Flask(__name__)
natcash = Natcash(app)


@app.get("/cb")
@natcash.callback
def flask_callback(callback: Callback) -> ResponseReturnValue:
    return status_name(callback)


parts = (natcash_callback, NatcashCallback)
