from collections.abc import Iterator

import django
import pytest
from django.conf import settings as django_settings
from django.test import AsyncRequestFactory, RequestFactory
from django_support import NATCASH, SettingsOverrides

if not django_settings.configured:
    django_settings.configure(
        SECRET_KEY="natcashify-tests",
        INSTALLED_APPS=["natcashify.django"],
        DATABASES={},
        USE_TZ=True,
    )
    django.setup()


@pytest.fixture
def settings() -> Iterator[SettingsOverrides]:
    overrides = SettingsOverrides()
    overrides.set(NATCASH=NATCASH)
    yield overrides
    overrides.restore()


@pytest.fixture
def rf() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def async_rf() -> AsyncRequestFactory:
    return AsyncRequestFactory()
