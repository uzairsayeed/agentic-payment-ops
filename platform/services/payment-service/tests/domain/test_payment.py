from decimal import Decimal
import pytest

from app.domain.payment import (
    InvalidPaymentTransition,
    Payment,
    PaymentStatus,
)

def test_new_payment_starts_in_created_state() -> None:
    payment = Payment.create(
        beneficiary_id="BEN-001",
        source_currency="usd",
        destination_currency="eur",
        amount=Decimal("1000.00"),
    )

    assert payment.status == PaymentStatus.CREATED

    assert payment.source_currency == "USD"
    assert payment.destination_currency == "EUR"

    assert payment.payment_id.startswith("PAY-")

    assert len(payment.events) == 1

    event = payment.events[0]

    assert event.event_type == "PAYMENT_CREATED"
    assert event.from_status is None
    assert event.to_status == PaymentStatus.CREATED

def test_payment_can_start_compliance() -> None:
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

    assert (
        payment.status
        == PaymentStatus.COMPLIANCE_PENDING
    )

    assert len(payment.events) == 2

    event = payment.events[-1]

    assert event.event_type == "COMPLIANCE_STARTED"

    assert event.from_status == PaymentStatus.CREATED

    assert (
        event.to_status
        == PaymentStatus.COMPLIANCE_PENDING
    )

def test_payment_cannot_jump_from_created_to_completed() -> None:
    payment = Payment.create(
        beneficiary_id="BEN-001",
        source_currency="USD",
        destination_currency="EUR",
        amount=Decimal("1000.00"),
    )

    with pytest.raises(
        InvalidPaymentTransition
    ):
        payment.transition_to(
            PaymentStatus.COMPLETED,
            event_type="PAYMENT_COMPLETED",
        )

def test_payment_cannot_jump_from_created_to_completed() -> None:
    payment = Payment.create(
        beneficiary_id="BEN-001",
        source_currency="USD",
        destination_currency="EUR",
        amount=Decimal("1000.00"),
    )

    with pytest.raises(
        InvalidPaymentTransition
    ):
        payment.transition_to(
            PaymentStatus.COMPLETED,
            event_type="PAYMENT_COMPLETED",
        )

    assert payment.status == PaymentStatus.CREATED

    assert len(payment.events) == 1

def test_payment_amount_must_be_positive() -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        Payment.create(
            beneficiary_id="BEN-001",
            source_currency="USD",
            destination_currency="EUR",
            amount=Decimal("0"),
        )