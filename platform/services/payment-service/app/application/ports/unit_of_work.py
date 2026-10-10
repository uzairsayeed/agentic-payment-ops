from types import TracebackType
from typing import Protocol

from app.application.ports.payment_repository import (
    PaymentRepository,
)


class UnitOfWork(Protocol):
    payments: PaymentRepository

    def __enter__(self) -> "UnitOfWork":
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...