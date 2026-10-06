from app.domain.payment import (
    Payment,
    PaymentEvent,
)

from app.infrastructure.persistence.models import (
    PaymentEventRecord,
    PaymentRecord,
)

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