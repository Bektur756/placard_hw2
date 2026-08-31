class CheckoutError(Exception):
    detail = "Checkout failed"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail

        super().__init__(self.detail)


class DuplicateSeatIdsError(CheckoutError):
    detail = "Seat ids must be unique"


class SeatsNotAvailableError(CheckoutError):
    detail = "Some seats are not available"


class PaymentUnavailableError(CheckoutError):
    detail = "Payment service unavailable"
