import inspect
import json
import logging
import math
import os
from collections.abc import Mapping, Sequence
from decimal import Decimal
from types import TracebackType
from typing import Final, Self

from natcashify.core import protocol
from natcashify.core.config import MerchantConfig, parse_bool
from natcashify.core.errors import APIError, ConfigurationError
from natcashify.core.http import (
    AsyncHttpTransport,
    AsyncUrllibTransport,
    HttpRequest,
    HttpResponse,
    HttpTransport,
    UrllibTransport,
)
from natcashify.core.models import Callback, Payment, Transaction

_LOG: Final = logging.getLogger("natcashify")
_DEFAULT_PREFIX: Final = "NATCASH_"


def _validated_timeout(timeout: float, name: str = "timeout") -> float:
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int | float)  # pyright: ignore[reportUnnecessaryIsInstance]
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise ConfigurationError(f"{name} must be a finite number greater than zero")
    return float(timeout)


def _env_timeout(key: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, str | int | float):
        raise ConfigurationError(f"{key} must be a number")
    try:
        number = float(value)
    except ValueError:
        raise ConfigurationError(f"{key} must be a number") from None
    return _validated_timeout(number, key)


def _env_settings(
    prefix: str, environ: Mapping[str, object] | None
) -> tuple[MerchantConfig, bool, float]:
    source = os.environ if environ is None else environ
    config = MerchantConfig.from_env(prefix, source)
    sandbox_key = f"{prefix}SANDBOX"
    timeout_key = f"{prefix}TIMEOUT"
    sandbox = parse_bool(sandbox_key, source[sandbox_key]) if sandbox_key in source else True
    timeout = (
        _env_timeout(timeout_key, source[timeout_key])
        if timeout_key in source
        else protocol.DEFAULT_TIMEOUT
    )
    return config, sandbox, timeout


def _log_request(request: HttpRequest, order_number: str, request_id: str) -> None:
    _LOG.debug(
        "NatCash request: POST %s order=%s request_id=%s", request.url, order_number, request_id
    )


def _envelope_status(response: HttpResponse) -> object:
    try:
        payload: object = json.loads(response.body)
    except (ValueError, RecursionError):
        return None
    if isinstance(payload, dict):
        status: object = payload.get("status")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        return status if isinstance(status, int) else None
    return None


def _log_response(response: HttpResponse, order_number: str) -> None:
    _LOG.debug(
        "NatCash response: http_status=%s order=%s status=%s",
        response.status,
        order_number,
        _envelope_status(response),
    )


def _check_order(transaction: Transaction, order_number: str, response: HttpResponse) -> None:
    if transaction.order_number != order_number:
        raise APIError(
            "NatCash API returned a transaction for a different order",
            http_status=response.status,
        )


class _ClientBase:
    def __init__(self, config: MerchantConfig, *, sandbox: bool, timeout: float) -> None:
        if not isinstance(sandbox, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ConfigurationError("sandbox must be True or False")
        self._config = config
        self._sandbox = sandbox
        self._timeout = _validated_timeout(timeout)
        self._base_url = protocol.SANDBOX_URL if sandbox else protocol.LIVE_URL

    @property
    def config(self) -> MerchantConfig:
        return self._config

    @property
    def sandbox(self) -> bool:
        return self._sandbox

    def verify_callback(self, order_number: str, code: int, signature: str) -> bool:
        return protocol.verify_callback(self._config, order_number, code, signature)

    def parse_callback(self, params: Mapping[str, str | Sequence[str]]) -> Callback:
        return protocol.parse_callback(self._config, params)

    def _payment_request(
        self,
        order_number: str,
        amount: Decimal | int,
        phone_number: str | None,
        *,
        skip_phone_input: bool,
    ) -> tuple[HttpRequest, str]:
        request_id = protocol.new_request_id()
        request = protocol.build_payment_request(
            self._config,
            base_url=self._base_url,
            timeout=self._timeout,
            order_number=order_number,
            amount=protocol.validate_payment(
                order_number, amount, phone_number, skip_phone_input=skip_phone_input
            ),
            phone_number=phone_number,
            skip_phone_input=skip_phone_input,
            request_id=request_id,
            timestamp=protocol.now_ms(),
        )
        _log_request(request, order_number, request_id)
        return request, request_id

    def _transaction_request(self, order_number: str, request_id: str | None) -> HttpRequest:
        used_id = request_id if request_id is not None else protocol.new_request_id()
        request = protocol.build_transaction_request(
            self._config,
            base_url=self._base_url,
            timeout=self._timeout,
            order_number=order_number,
            request_id=used_id,
        )
        _log_request(request, order_number, used_id)
        return request


class NatcashClient(_ClientBase):
    def __init__(
        self,
        config: MerchantConfig,
        *,
        sandbox: bool = True,
        timeout: float = protocol.DEFAULT_TIMEOUT,
        transport: HttpTransport | None = None,
    ) -> None:
        super().__init__(config, sandbox=sandbox, timeout=timeout)
        self._transport: HttpTransport = transport if transport is not None else UrllibTransport()

    @classmethod
    def from_env(
        cls,
        prefix: str = _DEFAULT_PREFIX,
        environ: Mapping[str, object] | None = None,
        *,
        transport: HttpTransport | None = None,
    ) -> Self:
        config, sandbox, timeout = _env_settings(prefix, environ)
        return cls(config, sandbox=sandbox, timeout=timeout, transport=transport)

    def create_payment(
        self,
        order_number: str,
        amount: Decimal | int,
        *,
        phone_number: str | None = None,
        skip_phone_input: bool = False,
    ) -> Payment:
        request, request_id = self._payment_request(
            order_number, amount, phone_number, skip_phone_input=skip_phone_input
        )
        response = self._transport.send(request)
        _log_response(response, order_number)
        return protocol.parse_payment_response(
            response, order_number=order_number, request_id=request_id
        )

    def get_transaction(self, order_number: str, *, request_id: str | None = None) -> Transaction:
        request = self._transaction_request(order_number, request_id)
        response = self._transport.send(request)
        _log_response(response, order_number)
        transaction = protocol.parse_transaction_response(response)
        _check_order(transaction, order_number, response)
        return transaction

    def close(self) -> None:
        closer = getattr(self._transport, "close", None)
        if callable(closer):
            closer()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


class AsyncNatcashClient(_ClientBase):
    def __init__(
        self,
        config: MerchantConfig,
        *,
        sandbox: bool = True,
        timeout: float = protocol.DEFAULT_TIMEOUT,
        transport: AsyncHttpTransport | None = None,
    ) -> None:
        super().__init__(config, sandbox=sandbox, timeout=timeout)
        self._transport: AsyncHttpTransport = (
            transport if transport is not None else AsyncUrllibTransport()
        )

    @classmethod
    def from_env(
        cls,
        prefix: str = _DEFAULT_PREFIX,
        environ: Mapping[str, object] | None = None,
        *,
        transport: AsyncHttpTransport | None = None,
    ) -> Self:
        config, sandbox, timeout = _env_settings(prefix, environ)
        return cls(config, sandbox=sandbox, timeout=timeout, transport=transport)

    async def create_payment(
        self,
        order_number: str,
        amount: Decimal | int,
        *,
        phone_number: str | None = None,
        skip_phone_input: bool = False,
    ) -> Payment:
        request, request_id = self._payment_request(
            order_number, amount, phone_number, skip_phone_input=skip_phone_input
        )
        response = await self._transport.send(request)
        _log_response(response, order_number)
        return protocol.parse_payment_response(
            response, order_number=order_number, request_id=request_id
        )

    async def get_transaction(
        self, order_number: str, *, request_id: str | None = None
    ) -> Transaction:
        request = self._transaction_request(order_number, request_id)
        response = await self._transport.send(request)
        _log_response(response, order_number)
        transaction = protocol.parse_transaction_response(response)
        _check_order(transaction, order_number, response)
        return transaction

    async def aclose(self) -> None:
        closer = getattr(self._transport, "aclose", None)
        if callable(closer):
            result = closer()
            if inspect.isawaitable(result):
                await result

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()
