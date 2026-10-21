from decimal import Decimal

from fastapi import FastAPI

from natcashify import AsyncNatcashClient, MerchantConfig
from natcashify.core.testing import AsyncFakeTransport, json_response, sign_callback
from natcashify.fastapi import NatcashCallback, get_async_natcash_client

ORDERS = {"ORDER-001": Decimal("250")}
CONFIG = MerchantConfig(
    private_key="private-key",
    partner_code="PARTNER",
    function_code="function-code",
    username="merchant",
    password="secret",
    callback_url="https://shop.example/natcash/callback",
)
TRANSPORT = AsyncFakeTransport(
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
CLIENT = AsyncNatcashClient(CONFIG, transport=TRANSPORT)

app = FastAPI()
app.dependency_overrides[get_async_natcash_client] = lambda: CLIENT


@app.get("/natcash/callback")
async def callback(callback: NatcashCallback) -> dict[str, str]:
    transaction = await CLIENT.get_transaction(callback.order_number)
    paid = transaction.is_successful and transaction.amount == ORDERS[callback.order_number]
    return {"order": callback.order_number, "status": "paid" if paid else "not paid"}


if __name__ == "__main__":
    from fastapi.testclient import TestClient

    signature = sign_callback(CONFIG, "ORDER-001", 1)
    query = {"orderNumber": "ORDER-001", "code": "1", "signature": signature}
    print(TestClient(app).get("/natcash/callback", params=query).json())
