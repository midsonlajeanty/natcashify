class NatcashError(Exception):
    pass


class ConfigurationError(NatcashError):
    pass


class InvalidPaymentError(NatcashError):
    pass


class InvalidSignatureError(NatcashError):
    pass


class TransportError(NatcashError):
    pass


class APIError(NatcashError):
    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        code: str | None = None,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.http_status = http_status


class TransactionNotFoundError(APIError):
    pass
