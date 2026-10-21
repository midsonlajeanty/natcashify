import os
from collections.abc import Mapping
from dataclasses import dataclass, fields
from enum import StrEnum
from urllib.parse import urlsplit

from natcashify.core.errors import ConfigurationError

_TRUE = frozenset({"true", "1", "yes", "on"})
_FALSE = frozenset({"false", "0", "no", "off"})
_CREDENTIALS = (
    "private_key",
    "partner_code",
    "function_code",
    "username",
    "password",
    "callback_url",
)
_MASKED = frozenset({"private_key", "password"})


class Language(StrEnum):
    HT = "ht"
    FR = "fr"
    EN = "en"


def parse_bool(name: str, value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUE:
            return True
        if lowered in _FALSE:
            return False
    raise ConfigurationError(
        f"{name} must be a boolean (true/false, 1/0, yes/no, on/off), got {value!r}"
    )


@dataclass(frozen=True, slots=True)
class MerchantConfig:
    private_key: str
    partner_code: str
    function_code: str
    username: str
    password: str
    callback_url: str
    payer_pays_fee: bool = True
    language: Language = Language.HT

    def __post_init__(self) -> None:
        for name in _CREDENTIALS:
            if not getattr(self, name):
                raise ConfigurationError(f"{name} must not be empty")
        parts = urlsplit(self.callback_url)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            raise ConfigurationError("callback_url must be an absolute http(s) URL")

    def __repr__(self) -> str:
        shown = ", ".join(
            f"{field.name}={'***' if field.name in _MASKED else repr(getattr(self, field.name))}"
            for field in fields(self)
        )
        return f"MerchantConfig({shown})"

    @classmethod
    def from_env(
        cls, prefix: str = "NATCASH_", environ: Mapping[str, object] | None = None
    ) -> "MerchantConfig":
        source = os.environ if environ is None else environ
        values: dict[str, str] = {}
        for name in _CREDENTIALS:
            key = f"{prefix}{name.upper()}"
            if key not in source:
                raise ConfigurationError(f"Missing environment variable {key}")
            values[name] = str(source[key])
        fee_key = f"{prefix}ENABLE_FEE"
        language_key = f"{prefix}LANGUAGE"
        try:
            language = Language(str(source.get(language_key, Language.HT.value)).strip().lower())
        except ValueError:
            raise ConfigurationError(f"{language_key} must be one of ht, fr, en") from None
        payer_pays_fee = parse_bool(fee_key, source[fee_key]) if fee_key in source else True
        return cls(**values, payer_pays_fee=payer_pays_fee, language=language)
