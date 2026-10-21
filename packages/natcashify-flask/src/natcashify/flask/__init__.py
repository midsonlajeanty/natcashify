from collections.abc import Callable
from functools import wraps
from typing import Concatenate, cast

from flask import Flask, abort, current_app, request
from flask.typing import ResponseReturnValue
from natcashify.core import Callback, HttpTransport, InvalidSignatureError, NatcashClient

__all__ = ["Natcash"]

EXTENSION_KEY = "natcashify"


class Natcash:
    def __init__(self, app: Flask | None = None, *, transport: HttpTransport | None = None) -> None:
        self._transport = transport
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        app.extensions[EXTENSION_KEY] = NatcashClient.from_env(
            environ=app.config, transport=self._transport
        )

    @property
    def client(self) -> NatcashClient:
        return cast("NatcashClient", current_app.extensions[EXTENSION_KEY])

    def callback[**P](
        self, view: Callable[Concatenate[Callback, P], ResponseReturnValue]
    ) -> Callable[P, ResponseReturnValue]:
        @wraps(view)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
            try:
                callback = self.client.parse_callback(request.args.to_dict(flat=False))
            except InvalidSignatureError:
                abort(400)
            return view(callback, *args, **kwargs)

        return wrapper
