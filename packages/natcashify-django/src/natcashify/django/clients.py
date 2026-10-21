from functools import lru_cache

from django.conf import settings
from django.core.signals import setting_changed
from natcashify.core import AsyncNatcashClient, NatcashClient


@lru_cache(maxsize=1)
def get_client() -> NatcashClient:
    return NatcashClient.from_env(prefix="", environ=settings.NATCASH)


@lru_cache(maxsize=1)
def get_async_client() -> AsyncNatcashClient:
    return AsyncNatcashClient.from_env(prefix="", environ=settings.NATCASH)


def reset_clients_on_setting_change(*, setting: str, **_: object) -> None:
    if setting == "NATCASH":
        get_client.cache_clear()
        get_async_client.cache_clear()


def connect_setting_changed() -> None:
    setting_changed.connect(reset_clients_on_setting_change)
