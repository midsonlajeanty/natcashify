from django.conf import settings
from django.core.checks import CheckMessage, Error
from natcashify.core import ConfigurationError, NatcashClient

HINT = (
    "Set NATCASH to a dict with PRIVATE_KEY, PARTNER_CODE, FUNCTION_CODE, USERNAME, PASSWORD "
    "and CALLBACK_URL."
)


def check_settings(**_: object) -> list[CheckMessage]:
    if not hasattr(settings, "NATCASH"):
        return [Error("NATCASH is not configured.", hint=HINT, id="natcashify.E001")]
    try:
        NatcashClient.from_env(prefix="", environ=settings.NATCASH)
    except ConfigurationError as error:
        return [Error(f"NATCASH is invalid: {error}", hint=HINT, id="natcashify.E001")]
    return []
