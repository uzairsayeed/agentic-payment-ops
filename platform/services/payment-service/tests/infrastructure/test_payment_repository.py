from decimal import Decimal

import pytest
from sqlalchemy import delete

from app.domain.payment import Payment, PaymentStatus
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    PaymentEventRecord,
    PaymentRecord,
)
from app.infrastructure.persistence.repository import (
    SqlAlchemyPaymentRepository,
)


@pytest.fixture
def persisted_payment_id() -> str:
    payment = Payment.create(
        beneficiary_id="BEN-INTEGRATION-001",
        source_currency="USD",
        destination_currency="EUR",
        amount=Decimal("1000.00"),
    )

    with SessionFactory.begin() as session:
        repository = SqlAlchemyPaymentRepository(session)
        repository.add(payment)

    payment.mark_events_persisted()

    try:
        yield payment.payment_id

    finally:
        with SessionFactory.begin() as session:
            session.execute(
                delete(PaymentEventRecord).where(
                    PaymentEventRecord.payment_id
                    == payment.payment_id
                )
            )

            session.execute(
                delete(PaymentRecord).where(
                    PaymentRecord.payment_id
                    == payment.payment_id
                )
            )


@pytest.mark.integration
def test_save_persists_state_and_new_event_atomically(
    persisted_payment_id: str,
) -> None:
    with SessionFactory.begin() as session:
        repository = SqlAlchemyPaymentRepository(session)

        payment = repository.get(
            persisted_payment_id
        )

        assert payment is not None
        assert payment.status == PaymentStatus.CREATED
        assert len(payment.events) == 1
        assert len(payment.pending_events) == 0

        payment.transition_to(
            PaymentStatus.COMPLIANCE_PENDING,
            event_type="COMPLIANCE_STARTED",
        )

        repository.save(payment)

    # The transaction has committed successfully.
    payment.mark_events_persisted()

    with SessionFactory() as session:
        repository = SqlAlchemyPaymentRepository(session)

        reloaded = repository.get(
            persisted_payment_id
        )

        assert reloaded is not None

        assert (
            reloaded.status
            == PaymentStatus.COMPLIANCE_PENDING
        )

        assert [
            event.event_type
            for event in reloaded.events
        ] == [
            "PAYMENT_CREATED",
            "COMPLIANCE_STARTED",
        ]

        assert len(reloaded.pending_events) == 0

@pytest.mark.integration
def test_failed_transaction_rolls_back_state_and_event(
    persisted_payment_id: str,
) -> None:
    payment_after_failure = None

    with pytest.raises(
        RuntimeError,
        match="forced transaction failure",
    ):
        with SessionFactory.begin() as session:
            repository = SqlAlchemyPaymentRepository(session)

            payment = repository.get(
                persisted_payment_id
            )

            assert payment is not None

            payment.transition_to(
                PaymentStatus.COMPLIANCE_PENDING,
                event_type="COMPLIANCE_STARTED",
            )

            repository.save(payment)

            # Force SQL to reach PostgreSQL while the
            # transaction is still uncommitted.
            session.flush()

            payment_after_failure = payment

            raise RuntimeError(
                "forced transaction failure"
            )

    assert payment_after_failure is not None

    assert (
        len(payment_after_failure.pending_events)
        == 1
    )