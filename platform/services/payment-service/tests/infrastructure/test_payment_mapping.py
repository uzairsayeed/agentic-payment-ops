from decimal import Decimal

from app.domain.payment import (
    Payment,
    PaymentStatus,
)
from app.infrastructure.persistence.repository import (
    to_domain_payment,
    to_event_record,
    to_payment_record,
)


def test_payment_round_trip_mapping() -> None:
    payment = Payment.create(
        beneficiary_id="BEN-001",
        source_currency="USD",
        destination_currency="EUR",
        amount=Decimal("1000.00"),
    )

    payment.transition_to(
        PaymentStatus.COMPLIANCE_PENDING,
        event_type="COMPLIANCE_STARTED",
    )

    payment_record = to_payment_record(payment)

    event_records = [
        to_event_record(
            payment.payment_id,
            event,
        )
        for event in payment.events
    ]

    restored = to_domain_payment(
        payment_record,
        event_records,
    )

    assert restored.payment_id == payment.payment_id
    assert restored.status == payment.status
    assert restored.amount == payment.amount

    assert len(restored.events) == 2

    assert (
        restored.events[-1].event_type
        == "COMPLIANCE_STARTED"
    )