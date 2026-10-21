import natcashify
import natcashify.core


def test_facade_exports_exactly_the_core_api() -> None:
    assert natcashify.__all__ == natcashify.core.__all__


def test_every_exported_name_is_the_core_object() -> None:
    for name in natcashify.core.__all__:
        assert getattr(natcashify, name) is getattr(natcashify.core, name)
