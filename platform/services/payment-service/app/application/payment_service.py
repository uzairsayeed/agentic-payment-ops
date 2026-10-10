from app.domain.payment import Payment, PaymentStatus
from collections.abc import Callable
from decimal import Decimal

from app.application.ports.unit_of_work import (
    UnitOfWork,
)

class PaymentNotFoundError(LookupError):
    pass


class PaymentApplicationService:
    def __init__(
        self,
        unit_of_work_factory: Callable[
            [], UnitOfWork
        ],
    ) -> None:
        self._unit_of_work_factory = (
            unit_of_work_factory
        )

    def create_payment(
        self,
        beneficiary_id: str,
        source_currency: str,
        destination_currency: str,
        amount: Decimal,
    ) -> Payment:
        # This invokes the domain.
        # After this line:
            # payment.status
            # =
            # CREATED
        # and conceptually:
            # events:
            # PAYMENT_CREATED

            # pending_events:
            # PAYMENT_CREATED
        payment = Payment.create(
            beneficiary_id=beneficiary_id,
            source_currency=source_currency,
            destination_currency=destination_currency,
            amount=amount,
        )

        # opens one persistence unit.
            # SqlAlchemyUnitOfWork
            #         ↓
            # SQLAlchemy Session
        with self._unit_of_work_factory() as uow:
            uow.payments.add(payment)

            uow.commit()

        payment.mark_events_persisted()

        return payment

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