import pytest
from fastapi.testclient import TestClient

from app.api.main import (
    app,
    get_payment_service,
)
from app.application.payment_service import (
    PaymentApplicationService,
)
from tests.fakes.payment_persistence import (
    FakePaymentRepository,
    FakeUnitOfWork,
)

# route needs PaymentApplicationService
#         ↓
# Depends(get_payment_service)
#         ↓
# FastAPI checks dependency_overrides
#         ↓
# "get_payment_service has an override"
#         ↓
# call lambda: service
#         ↓
# test PaymentApplicationService
#         ↓
# FakeUnitOfWork
#         ↓
# FakePaymentRepository
@pytest.fixture
def api_client():
    repository = FakePaymentRepository()

    service = PaymentApplicationService(
        unit_of_work_factory=lambda: FakeUnitOfWork(
            repository
        )
    )

    app.dependency_overrides[
        get_payment_service
    ] = lambda: service

    with TestClient(app) as client:
        yield client, repository

    app.dependency_overrides.clear()

def test_create_payment_returns_201(
    api_client,
) -> None:
    client, repository = api_client

    response = client.post(
        "/payments",
        json={
            "beneficiary_id": "BEN-API-001",
            "source_currency": "usd",
            "destination_currency": "eur",
            "amount": "500.25",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["beneficiary_id"] == "BEN-API-001"
    assert body["source_currency"] == "USD"
    assert body["destination_currency"] == "EUR"
    assert body["status"] == "CREATED"

    assert len(repository.added_payments) == 1
    
def test_create_payment_rejects_invalid_amount_schema(
    api_client,
) -> None:
    client, repository = api_client

    response = client.post(
        "/payments",
        json={
            "beneficiary_id": "BEN-API-002",
            "source_currency": "USD",
            "destination_currency": "EUR",
            "amount": "banana",
        },
    )

    assert response.status_code == 422

    assert repository.added_payments == []

def test_create_payment_rejects_negative_amount(
    api_client,
) -> None:
    client, repository = api_client

    response = client.post(
        "/payments",
        json={
            "beneficiary_id": "BEN-API-003",
            "source_currency": "USD",
            "destination_currency": "EUR",
            "amount": "-10.00",
        },
    )

    assert response.status_code == 400

    assert response.json()["error"] == (
        "INVALID_PAYMENT_DATA"
    )

    assert repository.added_payments == []

def test_get_missing_payment_returns_404(
    api_client,
) -> None:
    client, _ = api_client

    response = client.get(
        "/payments/PAY-DOES-NOT-EXIST"
    )

    assert response.status_code == 404

    assert response.json()["error"] == (
        "PAYMENT_NOT_FOUND"
    )

def test_start_compliance_updates_payment(
    api_client,
) -> None:
    client, _ = api_client

    create_response = client.post(
        "/payments",
        json={
            "beneficiary_id": "BEN-API-004",
            "source_currency": "USD",
            "destination_currency": "EUR",
            "amount": "700.00",
        },
    )

    payment_id = create_response.json()[
        "payment_id"
    ]

    compliance_response = client.post(
        f"/payments/{payment_id}/compliance"
    )

    assert compliance_response.status_code == 200
    assert (
        compliance_response.json()["status"]
        == "COMPLIANCE_PENDING"
    )

    get_response = client.get(
        f"/payments/{payment_id}"
    )

    assert get_response.status_code == 200
    assert (
        get_response.json()["status"]
        == "COMPLIANCE_PENDING"
    )

def test_start_compliance_twice_returns_409(
    api_client,
) -> None:
    client, _ = api_client

    create_response = client.post(
        "/payments",
        json={
            "beneficiary_id": "BEN-API-005",
            "source_currency": "USD",
            "destination_currency": "EUR",
            "amount": "900.00",
        },
    )

    payment_id = create_response.json()[
        "payment_id"
    ]

    first_response = client.post(
        f"/payments/{payment_id}/compliance"
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/payments/{payment_id}/compliance"
    )

    assert second_response.status_code == 409

    assert second_response.json()["error"] == (
        "INVALID_PAYMENT_TRANSITION"
    )