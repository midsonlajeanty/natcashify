from functools import cache
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from natcashify.core import AsyncNatcashClient, Callback, InvalidSignatureError, NatcashClient

__all__ = [
    "NatcashCallback",
    "get_async_natcash_client",
    "get_natcash_client",
    "natcash_callback",
]


@cache
def get_natcash_client() -> NatcashClient:
    return NatcashClient.from_env()


@cache
def get_async_natcash_client() -> AsyncNatcashClient:
    return AsyncNatcashClient.from_env()


async def natcash_callback(
    request: Request,
    client: Annotated[AsyncNatcashClient, Depends(get_async_natcash_client)],
) -> Callback:
    params: dict[str, list[str]] = {}
    for key, value in request.query_params.multi_items():
        params.setdefault(key, []).append(value)
    try:
        return client.parse_callback(params)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid NatCash callback") from None


NatcashCallback = Annotated[Callback, Depends(natcash_callback)]
