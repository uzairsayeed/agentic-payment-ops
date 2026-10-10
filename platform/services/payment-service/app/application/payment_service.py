from app.domain.payment import Payment, PaymentStatus
from app.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

class PaymentNotFoundError(LookupError):
    pass


class PaymentApplicationService:
    def __init__(
        self,
        unit_of_work_factory=SqlAlchemyUnitOfWork,
    ) -> None:
        self._unit_of_work_factory = (
            unit_of_work_factory
        )

    def start_compliance(
        self,
        payment_id: str,
    ) -> Payment:
        with self._unit_of_work_factory() as uow:
            # uow
            # ↓
            # SqlAlchemyUnitOfWork instance

            # uow.payments
            # ↓
            # SqlAlchemyPaymentRepository instance

            # uow.payments.save(payment)
            # ↓
            # call save() on that repository
            payment = uow.payments.get(
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

            uow.payments.save(payment)

            uow.commit()

        payment.mark_events_persisted()

        return payment