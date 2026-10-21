from typing import Any

import pytest

from natcashify.core.config import Language, MerchantConfig, parse_bool
from natcashify.core.errors import ConfigurationError

VALID: dict[str, Any] = {
    "private_key": "secret-key",
    "partner_code": "P1",
    "function_code": "F1",
    "username": "user",
    "password": "hunter2",
    "callback_url": "https://shop.example/callback",
}

ENV = {
    "NATCASH_PRIVATE_KEY": "k",
    "NATCASH_PARTNER_CODE": "P1",
    "NATCASH_FUNCTION_CODE": "F1",
    "NATCASH_USERNAME": "u",
    "NATCASH_PASSWORD": "p",
    "NATCASH_CALLBACK_URL": "https://shop.example/cb",
}


def build(overrides: dict[str, Any] | None = None) -> MerchantConfig:
    values: dict[str, Any] = {**VALID, **(overrides or {})}
    return MerchantConfig(**values)


@pytest.mark.parametrize("field", list(VALID))
def test_empty_credentials_are_rejected(field: str) -> None:
    with pytest.raises(ConfigurationError, match=field):
        build({field: ""})


@pytest.mark.parametrize(
    "url", ["shop.example/cb", "ftp://shop.example/cb", "https://", "javascript:alert(1)"]
)
def test_callback_url_must_be_absolute_http(url: str) -> None:
    with pytest.raises(ConfigurationError, match="callback_url"):
        build({"callback_url": url})


def test_defaults() -> None:
    config = build()
    assert config.payer_pays_fee is True
    assert config.language is Language.HT


def test_repr_masks_secrets() -> None:
    text = repr(build())
    assert VALID["private_key"] not in text
    assert VALID["password"] not in text
    assert "partner_code='P1'" in text


def test_from_env_reads_the_laravel_variable_names() -> None:
    config = MerchantConfig.from_env(
        environ={**ENV, "NATCASH_ENABLE_FEE": "false", "NATCASH_LANGUAGE": "fr"}
    )
    assert config.private_key == "k"
    assert config.callback_url == "https://shop.example/cb"
    assert config.payer_pays_fee is False
    assert config.language is Language.FR


def test_from_env_defaults_fee_and_language() -> None:
    config = MerchantConfig.from_env(environ=ENV)
    assert config.payer_pays_fee is True
    assert config.language is Language.HT


def test_from_env_supports_a_custom_prefix() -> None:
    environ = {key.replace("NATCASH_", "SHOP_"): value for key, value in ENV.items()}
    assert MerchantConfig.from_env("SHOP_", environ).partner_code == "P1"


def test_from_env_reads_os_environ_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    assert MerchantConfig.from_env().username == "u"


def test_from_env_names_the_missing_variable() -> None:
    environ = {key: value for key, value in ENV.items() if key != "NATCASH_PASSWORD"}
    with pytest.raises(ConfigurationError, match="NATCASH_PASSWORD"):
        MerchantConfig.from_env(environ=environ)


def test_from_env_rejects_unknown_language_and_bool() -> None:
    with pytest.raises(ConfigurationError, match="NATCASH_LANGUAGE"):
        MerchantConfig.from_env(environ={**ENV, "NATCASH_LANGUAGE": "es"})
    with pytest.raises(ConfigurationError, match="NATCASH_ENABLE_FEE"):
        MerchantConfig.from_env(environ={**ENV, "NATCASH_ENABLE_FEE": "maybe"})


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (False, False),
        ("TRUE", True),
        ("1", True),
        ("Yes", True),
        ("on", True),
        ("false", False),
        ("0", False),
        ("No", False),
        ("OFF", False),
    ],
)
def test_parse_bool_accepts_common_spellings(value: object, expected: bool) -> None:
    assert parse_bool("flag", value) is expected


@pytest.mark.parametrize("value", ["maybe", "", 1, None])
def test_parse_bool_rejects_everything_else(value: object) -> None:
    with pytest.raises(ConfigurationError, match="flag"):
        parse_bool("flag", value)


@pytest.mark.parametrize("field", list(VALID))
@pytest.mark.parametrize("value", ["   ", "\t\n", None, 0, b"key"])
def test_blank_or_non_string_credentials_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ConfigurationError, match=field):
        build({field: value})


@pytest.mark.parametrize("value", [None, 0, 12345, b"F1", ["F1"]])
def test_from_env_rejects_non_string_values_without_echoing_them(value: object) -> None:
    with pytest.raises(ConfigurationError, match="NATCASH_FUNCTION_CODE") as caught:
        MerchantConfig.from_env(environ={**ENV, "NATCASH_FUNCTION_CODE": value})
    assert "None" not in str(caught.value)
    assert "12345" not in str(caught.value)


@pytest.mark.parametrize("value", ["", "   ", "\t"])
def test_from_env_rejects_blank_values(value: str) -> None:
    with pytest.raises(ConfigurationError, match="NATCASH_PASSWORD"):
        MerchantConfig.from_env(environ={**ENV, "NATCASH_PASSWORD": value})


def test_from_env_never_echoes_a_rejected_secret() -> None:
    with pytest.raises(ConfigurationError) as caught:
        MerchantConfig.from_env(environ={**ENV, "NATCASH_PRIVATE_KEY": "  "})
    assert "NATCASH_PRIVATE_KEY" in str(caught.value)
    assert "'  '" not in str(caught.value)
