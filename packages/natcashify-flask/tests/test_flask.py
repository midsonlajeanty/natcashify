import pytest
from flask import Flask
from flask.typing import ResponseReturnValue
from php_vectors import CONFIG, VECTORS

from natcashify.core import Callback, ConfigurationError, NatcashClient
from natcashify.core.testing import FakeTransport
from natcashify.flask import Natcash

VECTOR = VECTORS["callbacks"][0]
QUERY = {
    "orderNumber": VECTOR["order_number"],
    "code": str(VECTOR["code"]),
    "signature": VECTOR["signature"],
}
CONFIG_KEYS = {
    "NATCASH_PRIVATE_KEY": CONFIG.private_key,
    "NATCASH_PARTNER_CODE": CONFIG.partner_code,
    "NATCASH_FUNCTION_CODE": CONFIG.function_code,
    "NATCASH_USERNAME": CONFIG.username,
    "NATCASH_PASSWORD": CONFIG.password,
    "NATCASH_CALLBACK_URL": CONFIG.callback_url,
}


def make_app(**extra: object) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(CONFIG_KEYS)
    app.config.from_mapping(extra)
    return app


def test_init_app_registers_the_client() -> None:
    app = make_app()
    natcash = Natcash(app, transport=FakeTransport())
    client = app.extensions["natcashify"]
    assert isinstance(client, NatcashClient)
    assert client.config.username == CONFIG.username
    assert client.sandbox is True
    with app.app_context():
        assert natcash.client is client


def test_app_factory_pattern() -> None:
    natcash = Natcash()
    first = make_app(NATCASH_LANGUAGE="fr")
    second = make_app(NATCASH_LANGUAGE="en")
    natcash.init_app(first)
    natcash.init_app(second)
    assert first.extensions["natcashify"] is not second.extensions["natcashify"]
    with first.app_context():
        assert natcash.client.config.language.value == "fr"
    with second.app_context():
        assert natcash.client.config.language.value == "en"


def make_callback_app() -> Flask:
    app = make_app()
    natcash = Natcash(app, transport=FakeTransport())

    @app.get("/callback")
    @natcash.callback
    def callback(callback: Callback) -> ResponseReturnValue:
        return f"{callback.order_number}:{callback.status.name}"

    return app


def test_callback_decorator_passes_a_verified_callback() -> None:
    response = make_callback_app().test_client().get("/callback", query_string=QUERY)
    assert response.status_code == 200
    assert response.get_data(as_text=True).startswith(f"{VECTOR['order_number']}:")


def test_callback_decorator_rejects_a_bad_signature() -> None:
    response = (
        make_callback_app().test_client().get("/callback", query_string={**QUERY, "signature": "x"})
    )
    assert response.status_code == 400


def test_callback_decorator_rejects_repeated_parameters() -> None:
    query = f"orderNumber={QUERY['orderNumber']}&code=1&code=-1&signature={QUERY['signature']}"
    response = make_callback_app().test_client().get("/callback", query_string=query)
    assert response.status_code == 400


def test_missing_config_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        Natcash(Flask(__name__))


def test_client_explains_a_missing_init_app() -> None:
    natcash = Natcash(transport=FakeTransport())
    app = make_app()
    with app.app_context(), pytest.raises(RuntimeError, match="init_app"):
        natcash.client  # noqa: B018
