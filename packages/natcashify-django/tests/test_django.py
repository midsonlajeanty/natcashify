from django.core.checks import run_checks
from django.http import HttpRequest, HttpResponse
from django.test import AsyncRequestFactory, RequestFactory
from django_support import SettingsOverrides
from php_vectors import VECTORS

from natcashify.core import Callback, TransactionStatus
from natcashify.django import get_async_client, get_client, natcash_callback
from natcashify.django.checks import check_settings

VECTOR = VECTORS["callbacks"][0]
QUERY = {
    "orderNumber": VECTOR["order_number"],
    "code": str(VECTOR["code"]),
    "signature": VECTOR["signature"],
}


def test_get_client_builds_from_settings(settings: SettingsOverrides) -> None:
    settings.set(NATCASH={**settings.base, "LANGUAGE": "fr"})
    client = get_client()
    assert client is get_client()
    assert client.config.language.value == "fr"
    assert client.sandbox is True
    assert get_async_client() is get_async_client()


def test_settings_change_resets_the_cached_client(settings: SettingsOverrides) -> None:
    first = get_client()
    first_async = get_async_client()
    settings.set(NATCASH={**settings.base, "SANDBOX": False})
    assert get_client() is not first
    assert get_client().sandbox is False
    assert get_async_client() is not first_async


def test_unrelated_setting_change_keeps_the_cached_client(settings: SettingsOverrides) -> None:
    first = get_client()
    settings.set(DEBUG=True)
    assert get_client() is first


def test_check_accepts_valid_settings(settings: SettingsOverrides) -> None:
    assert check_settings() == []


def test_check_reports_missing_settings(settings: SettingsOverrides) -> None:
    settings.delete("NATCASH")
    [error] = check_settings()
    assert error.id == "natcashify.E001"


def test_check_reports_invalid_settings(settings: SettingsOverrides) -> None:
    settings.set(NATCASH={"PRIVATE_KEY": "k"})
    [error] = check_settings()
    assert error.id == "natcashify.E001"
    assert "NATCASH is invalid" in error.msg


def test_check_reports_a_non_dict_setting(settings: SettingsOverrides) -> None:
    settings.set(NATCASH="nope")
    [error] = check_settings()
    assert error.id == "natcashify.E001"


def test_check_is_registered(settings: SettingsOverrides) -> None:
    settings.delete("NATCASH")
    assert "natcashify.E001" in [message.id for message in run_checks()]


@natcash_callback
def view(request: HttpRequest, callback: Callback) -> HttpResponse:
    return HttpResponse(f"{callback.order_number}:{callback.status.name}")


def test_callback_view_passes_a_verified_callback(
    rf: RequestFactory, settings: SettingsOverrides
) -> None:
    response = view(rf.get("/callback", QUERY))
    assert response.status_code == 200
    assert response.content.decode() == f"ORDER-001:{TransactionStatus.from_code(1).name}"


def test_callback_view_rejects_a_bad_signature(
    rf: RequestFactory, settings: SettingsOverrides
) -> None:
    response = view(rf.get("/callback", {**QUERY, "signature": "0" * 64}))
    assert response.status_code == 400


def test_callback_view_rejects_repeated_parameters(
    rf: RequestFactory, settings: SettingsOverrides
) -> None:
    response = view(rf.get("/callback", {**QUERY, "code": [QUERY["code"], "2"]}))
    assert response.status_code == 400


@natcash_callback
async def async_view(request: HttpRequest, callback: Callback) -> HttpResponse:
    return HttpResponse(callback.order_number)


async def test_async_callback_view(
    async_rf: AsyncRequestFactory, settings: SettingsOverrides
) -> None:
    get_client.cache_clear()
    get_async_client.cache_clear()
    good = await async_view(async_rf.get("/callback", QUERY))
    assert get_async_client.cache_info().currsize == 1
    assert get_client.cache_info().currsize == 0
    bad = await async_view(async_rf.get("/callback", {**QUERY, "signature": "0" * 64}))
    assert (good.status_code, good.content) == (200, b"ORDER-001")
    assert bad.status_code == 400
