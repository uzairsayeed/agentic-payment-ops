# what is a Unit of Work?
    # A Unit of Work represents: A set of persistence operations that must succeed or fail as one business transaction.
    # Application use case
    #     ↓
    # Unit of Work
    #     │
    #     ├── PaymentRepository
    #     │
    #     └── transaction lifecycle
    #             ↓
    #         PostgreSQL

# Important distinction: Repository vs Unit of Work
    # Repository answers: How do I load and persist a Payment?
    # Unit of Work answers: Which repository operations belong to the same transaction?
from types import TracebackType

from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repository import (
    SqlAlchemyPaymentRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(
        self,
        session_factory=SessionFactory,
    ) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()

        self.payments = SqlAlchemyPaymentRepository(
            self.session
        )

        return self

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()

        self.session.close()