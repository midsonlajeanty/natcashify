from django.apps import AppConfig
from django.core import checks


class NatcashConfig(AppConfig):
    name = "natcashify.django"
    label = "natcashify"
    verbose_name = "Natcashify"

    def ready(self) -> None:
        from natcashify.django.checks import check_settings  # noqa: PLC0415
        from natcashify.django.clients import connect_setting_changed  # noqa: PLC0415

        connect_setting_changed()
        checks.register(check_settings)
