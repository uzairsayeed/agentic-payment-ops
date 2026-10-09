from app.domain.payment import (
    Payment,
    PaymentEvent,
)

from app.infrastructure.persistence.models import (
    PaymentEventRecord,
    PaymentRecord,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

def to_payment_record(
    payment: Payment,
) -> PaymentRecord:
    return PaymentRecord(
        payment_id=payment.payment_id,
        beneficiary_id=payment.beneficiary_id,
        source_currency=payment.source_currency,
        destination_currency=payment.destination_currency,
        amount=payment.amount,
        status=payment.status,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )

def to_event_record(
    payment_id: str,
    event: PaymentEvent,
) -> PaymentEventRecord:
    return PaymentEventRecord(
        payment_id=payment_id,
        event_type=event.event_type,
        from_status=event.from_status,
        to_status=event.to_status,
        occurred_at=event.occurred_at,
    )

def to_payment_event(
    record: PaymentEventRecord,
) -> PaymentEvent:
    return PaymentEvent(
        event_type=record.event_type,
        from_status=record.from_status,
        to_status=record.to_status,
        occurred_at=record.occurred_at,
    )

def to_domain_payment(
    record: PaymentRecord,
    event_records: list[PaymentEventRecord],
) -> Payment:
    events = [
        to_payment_event(event)
        for event in event_records
    ]

    return Payment.restore(
        payment_id=record.payment_id,
        beneficiary_id=record.beneficiary_id,
        source_currency=record.source_currency,
        destination_currency=record.destination_currency,
        amount=record.amount,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
        events=events,
    )

class SqlAlchemyPaymentRepository:
    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    # add() should NOT call commit()
    # We deliberately will not do that.
    # Why?
        # Imagine later creating a payment requires:
            # insert payment
            # insert payment event
            # write audit record
            # create some other record
        # We may want: ALL succeed or ALL rollback
        # If the repository internally commits after one step, the higher-level application cannot control atomicity.
        # So our repository means:
            # Stage database work in the current Session.

        # It does not mean:
            # Decide when the business transaction is finished.
    def add(
        self,
        payment: Payment,
    ) -> None:
        payment_record = to_payment_record(
            payment
        )

        self._session.add(
            payment_record
        )

        # Push the parent INSERT to PostgreSQL first
        # so the FK target exists before event rows are inserted.
        # flush() is NOT commit()
        # Explanation:
            # session.add()
            #     ↓
            # Python Session knows about new object

            # session.flush()
            #     ↓
            # SQL is sent to PostgreSQL
            # BUT transaction is still open

            # session.commit()
            #     ↓
            # transaction becomes permanent

        # Why not just commit() after inserting the payment?
            # That would be wrong:
                # INSERT payment
                # COMMIT              ← payment permanent

                # INSERT event
                # FAIL
        self._session.flush()

        for event in payment.pending_events:
            self._session.add(
                to_event_record(
                    payment.payment_id,
                    event,
                )
            )

    def get(
        self,
        payment_id: str,
    ) -> Payment | None:
        payment_record = self._session.get(
            PaymentRecord,
            payment_id,
        )

        if payment_record is None:
            return None

        event_records = list(
            self._session.scalars(
                select(PaymentEventRecord)
                .where(
                    PaymentEventRecord.payment_id
                    == payment_id
                )
                .order_by(
                    PaymentEventRecord.occurred_at,
                    PaymentEventRecord.id,
                )
            )
        )

        return to_domain_payment(
            payment_record,
            event_records,
        )

    def save(
        self,
        payment: Payment,
    ) -> None:
        payment_record = self._session.get(
            PaymentRecord,
            payment.payment_id,
        )

        if payment_record is None:
            raise LookupError(
                f"Payment {payment.payment_id} does not exist."
            )

        payment_record.beneficiary_id = payment.beneficiary_id
        payment_record.source_currency = payment.source_currency
        payment_record.destination_currency = payment.destination_currency
        payment_record.amount = payment.amount
        payment_record.status = payment.status
        payment_record.updated_at = payment.updated_at

        for event in payment.pending_events:
            self._session.add(
                to_event_record(
                    payment.payment_id,
                    event,
                )
            )