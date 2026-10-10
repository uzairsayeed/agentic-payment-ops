from decimal import Decimal

import pytest

from app.application.payment_service import (
    PaymentApplicationService,
    PaymentNotFoundError,
)
from app.domain.payment import (
    InvalidPaymentTransition,
    Payment,
    PaymentStatus,
)


class FakePaymentRepository:
    def __init__(
        self,
        payments: list[Payment] | None = None,
    ) -> None:
        self._payments = {
            payment.payment_id: payment
            for payment in (payments or [])
        }

        self.saved_payments: list[Payment] = []

    def add(
        self,
        payment: Payment,
    ) -> None:
        self._payments[payment.payment_id] = payment

    def get(
        self,
        payment_id: str,
    ) -> Payment | None:
        return self._payments.get(payment_id)

    def save(
        self,
        payment: Payment,
    ) -> None:
        self._payments[payment.payment_id] = payment
        self.saved_payments.append(payment)


class FakeUnitOfWork:
    def __init__(
        self,
        payments: FakePaymentRepository,
    ) -> None:
        self.payments = payments
        self.committed = False
        self.rolled_back = False

    def __enter__(self) -> "FakeUnitOfWork":
        return self

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        if exc_type is not None:
            self.rollback()


def test_start_compliance_saves_and_commits() -> None:
    payment = Payment.create(
        beneficiary_id="BEN-001",
        source_currency="USD",
        destination_currency="EUR",
        amount=Decimal("1000.00"),
    )

    payment.mark_events_persisted()

    repository = FakePaymentRepository(
        payments=[payment]
    )

    uow = FakeUnitOfWork(
        payments=repository
    )

    service = PaymentApplicationService(
        unit_of_work_factory=lambda: uow
    )

    result = service.start_compliance(
        payment.payment_id
    )

    assert (
        result.status
        == PaymentStatus.COMPLIANCE_PENDING
    )

    assert [
        event.event_type
        for event in result.events
    ] == [
        "PAYMENT_CREATED",
        "COMPLIANCE_STARTED",
    ]

    assert len(repository.saved_payments) == 1

    assert uow.committed is True
    assert uow.rolled_back is False

    assert len(result.pending_events) == 0


def test_start_compliance_does_not_commit_when_payment_missing() -> None:
    repository = FakePaymentRepository()

    uow = FakeUnitOfWork(
        payments=repository
    )

    service = PaymentApplicationService(
        unit_of_work_factory=lambda: uow
    )

    with pytest.raises(PaymentNotFoundError):
        service.start_compliance(
            "PAY-DOES-NOT-EXIST"
        )

    assert uow.committed is False
    assert uow.rolled_back is True

    assert repository.saved_payments == []


def test_start_compliance_does_not_commit_invalid_transition() -> None:
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

    payment.mark_events_persisted()

    repository = FakePaymentRepository(
        payments=[payment]
    )

    uow = FakeUnitOfWork(
        payments=repository
    )

    service = PaymentApplicationService(
        unit_of_work_factory=lambda: uow
    )

    with pytest.raises(InvalidPaymentTransition):
        service.start_compliance(
            payment.payment_id
        )

    assert uow.committed is False
    assert uow.rolled_back is True

    assert repository.saved_payments == []