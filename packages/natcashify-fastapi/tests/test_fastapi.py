import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from php_vectors import CONFIG, VECTORS

from natcashify.core import AsyncNatcashClient
from natcashify.core.testing import AsyncFakeTransport
from natcashify.fastapi import (
    NatcashCallback,
    get_async_natcash_client,
    get_natcash_client,
)

VECTOR = VECTORS["callbacks"][0]
QUERY = {
    "orderNumber": VECTOR["order_number"],
    "code": str(VECTOR["code"]),
    "signature": VECTOR["signature"],
}
ENV = {
    "NATCASH_PRIVATE_KEY": CONFIG.private_key,
    "NATCASH_PARTNER_CODE": CONFIG.partner_code,
    "NATCASH_FUNCTION_CODE": CONFIG.function_code,
    "NATCASH_USERNAME": CONFIG.username,
    "NATCASH_PASSWORD": CONFIG.password,
    "NATCASH_CALLBACK_URL": CONFIG.callback_url,
}


def make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/callback")
    async def callback(callback: NatcashCallback) -> dict[str, str]:
        return {"order": callback.order_number, "status": callback.status.name}

    app.dependency_overrides[get_async_natcash_client] = lambda: AsyncNatcashClient.from_env(
        environ=ENV, transport=AsyncFakeTransport()
    )
    return app


def test_callback_dependency_yields_a_verified_callback() -> None:
    response = TestClient(make_app()).get("/callback", params=QUERY)
    assert response.status_code == 200
    assert response.json()["order"] == VECTOR["order_number"]


def test_callback_dependency_rejects_bad_signature() -> None:
    response = TestClient(make_app()).get("/callback", params={**QUERY, "signature": "bad"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid NatCash callback"}


def test_callback_dependency_rejects_repeated_parameters() -> None:
    response = TestClient(make_app()).get(
        f"/callback?orderNumber={QUERY['orderNumber']}&code=1&code=-1&signature={QUERY['signature']}"
    )
    assert response.status_code == 400


def test_client_dependency_reads_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    get_natcash_client.cache_clear()
    get_async_natcash_client.cache_clear()
    try:
        assert get_natcash_client() is get_natcash_client()
        assert get_natcash_client().config.username == CONFIG.username
        assert get_async_natcash_client().config.username == CONFIG.username
    finally:
        get_natcash_client.cache_clear()
        get_async_natcash_client.cache_clear()
