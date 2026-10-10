from app.domain.payment import Payment, PaymentStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.repository import (
    SqlAlchemyPaymentRepository,
)


class PaymentNotFoundError(LookupError):
    pass


class PaymentApplicationService:
    def __init__(
        self,
        session_factory=SessionFactory,
    ) -> None:
        self._session_factory = session_factory

    def start_compliance(
        self,
        payment_id: str,
    ) -> Payment:
        with self._session_factory.begin() as session:
            repository = SqlAlchemyPaymentRepository(
                session
            )

            payment = repository.get(
                payment_id
            )

            if payment is None:
                raise PaymentNotFoundError(
                    f"Payment {payment_id} does not exist."
                )

            payment.transition_to(
                PaymentStatus.COMPLIANCE_PENDING,
                event_type="COMPLIANCE_STARTED",
            )

            repository.save(payment)

        # Reaching here means the transaction committed.
        payment.mark_events_persisted()

        return payment