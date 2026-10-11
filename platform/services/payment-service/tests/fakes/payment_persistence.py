from app.domain.payment import Payment


class FakePaymentRepository:
    def __init__(
        self,
        payments: list[Payment] | None = None,
    ) -> None:
        self._payments = {
            payment.payment_id: payment
            for payment in (payments or [])
        }

        self.added_payments: list[Payment] = []
        self.saved_payments: list[Payment] = []

    def add(
        self,
        payment: Payment,
    ) -> None:
        self._payments[payment.payment_id] = payment
        self.added_payments.append(payment)

    def get(
        self,
        payment_id: str,
    ) -> Payment | None:
        return self._payments.get(payment_id)

    def save(
        self,
        payment: Payment,
    ) -> None:
        self._payments[payment.payment_id] = payment
        self.saved_payments.append(payment)


class FakeUnitOfWork:
    def __init__(
        self,
        payments: FakePaymentRepository,
    ) -> None:
        self.payments = payments
        self.committed = False
        self.rolled_back = False

    def __enter__(self) -> "FakeUnitOfWork":
        return self

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if exc_type is not None:
            self.rollback()