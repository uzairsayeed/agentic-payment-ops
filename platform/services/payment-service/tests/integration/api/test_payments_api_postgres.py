import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

from app.api.main import (
    app,
    get_payment_service,
)
from app.application.payment_service import (
    PaymentApplicationService,
)
from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.models import (
    PaymentEventRecord,
    PaymentRecord,
)
from app.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

# pytest starts
#     ↓
# create test engine once
#     ↓
# all integration tests use it
#     ↓
# pytest finishes
#     ↓
# drop test tables
#     ↓
# dispose engine
@pytest.fixture(scope="session")
def test_engine():
    database_url = os.environ["TEST_DATABASE_URL"]

    engine = create_engine(
        database_url,
    )

    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)

    engine.dispose()

@pytest.fixture
def test_session_factory(
    test_engine,
):
    session_factory = sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
    )

    with session_factory.begin() as session:
        session.execute(
            delete(PaymentEventRecord)
        )
        session.execute(
            delete(PaymentRecord)
        )

    yield session_factory

    with session_factory.begin() as session:
        session.execute(
            delete(PaymentEventRecord)
        )
        session.execute(
            delete(PaymentRecord)
        )

@pytest.fixture
def integration_client(
    test_session_factory,
):
    service = PaymentApplicationService(
        unit_of_work_factory=lambda: (
            SqlAlchemyUnitOfWork(
                session_factory=test_session_factory
            )
        )
    )

    app.dependency_overrides[
        get_payment_service
    ] = lambda: service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()

@pytest.mark.integration
def test_create_payment_persists_to_postgres(
    integration_client,
    test_session_factory,
) -> None:
    response = integration_client.post(
        "/payments",
        json={
            "beneficiary_id": "BEN-INT-001",
            "source_currency": "usd",
            "destination_currency": "eur",
            "amount": "500.25",
        },
    )

    assert response.status_code == 201

    body = response.json()
    payment_id = body["payment_id"]

    with test_session_factory() as session:
        payment_record = session.get(
            PaymentRecord,
            payment_id,
        )

        events = session.scalars(
            select(PaymentEventRecord)
            .where(
                PaymentEventRecord.payment_id
                == payment_id
            )
            .order_by(PaymentEventRecord.id)
        ).all()

    assert payment_record is not None

    assert (
        payment_record.beneficiary_id
        == "BEN-INT-001"
    )

    assert payment_record.source_currency == "USD"
    assert payment_record.destination_currency == "EUR"

    assert payment_record.status.value == "CREATED"

    assert len(events) == 1
    assert events[0].event_type == "PAYMENT_CREATED"

@pytest.mark.integration
def test_start_compliance_persists_state_and_event(
    integration_client,
    test_session_factory,
) -> None:
    create_response = integration_client.post(
        "/payments",
        json={
            "beneficiary_id": "BEN-INT-002",
            "source_currency": "USD",
            "destination_currency": "EUR",
            "amount": "700.00",
        },
    )

    assert create_response.status_code == 201

    payment_id = create_response.json()[
        "payment_id"
    ]

    compliance_response = integration_client.post(
        f"/payments/{payment_id}/compliance"
    )

    assert compliance_response.status_code == 200
    assert (
        compliance_response.json()["status"]
        == "COMPLIANCE_PENDING"
    )

    with test_session_factory() as session:
        payment_record = session.get(
            PaymentRecord,
            payment_id,
        )

        events = session.scalars(
            select(PaymentEventRecord)
            .where(
                PaymentEventRecord.payment_id
                == payment_id
            )
            .order_by(PaymentEventRecord.id)
        ).all()

    assert payment_record is not None

    assert (
        payment_record.status.value
        == "COMPLIANCE_PENDING"
    )

    assert [
        event.event_type
        for event in events
    ] == [
        "PAYMENT_CREATED",
        "COMPLIANCE_STARTED",
    ]

@pytest.mark.integration
def test_duplicate_start_compliance_does_not_add_event(
    integration_client,
    test_session_factory,
) -> None:
    create_response = integration_client.post(
        "/payments",
        json={
            "beneficiary_id": "BEN-INT-003",
            "source_currency": "USD",
            "destination_currency": "EUR",
            "amount": "900.00",
        },
    )

    payment_id = create_response.json()[
        "payment_id"
    ]

    first_response = integration_client.post(
        f"/payments/{payment_id}/compliance"
    )

    assert first_response.status_code == 200

    second_response = integration_client.post(
        f"/payments/{payment_id}/compliance"
    )

    assert second_response.status_code == 409

    with test_session_factory() as session:
        payment_record = session.get(
            PaymentRecord,
            payment_id,
        )

        events = session.scalars(
            select(PaymentEventRecord)
            .where(
                PaymentEventRecord.payment_id
                == payment_id
            )
            .order_by(PaymentEventRecord.id)
        ).all()

    assert payment_record is not None

    assert (
        payment_record.status.value
        == "COMPLIANCE_PENDING"
    )

    assert [
        event.event_type
        for event in events
    ] == [
        "PAYMENT_CREATED",
        "COMPLIANCE_STARTED",
    ]