from typing import Any

from django.conf import settings as django_settings
from django.test.utils import override_settings
from php_vectors import CONFIG

NATCASH: dict[str, Any] = {
    "PRIVATE_KEY": CONFIG.private_key,
    "PARTNER_CODE": CONFIG.partner_code,
    "FUNCTION_CODE": CONFIG.function_code,
    "USERNAME": CONFIG.username,
    "PASSWORD": CONFIG.password,
    "CALLBACK_URL": CONFIG.callback_url,
}


class SettingsOverrides:
    base = NATCASH

    def __init__(self) -> None:
        self._stack: list[override_settings] = []

    def set(self, **values: object) -> None:
        override = override_settings(**values)
        override.enable()
        self._stack.append(override)

    def delete(self, name: str) -> None:
        self.set(**{name: None})
        delattr(django_settings, name)

    def restore(self) -> None:
        while self._stack:
            self._stack.pop().disable()
