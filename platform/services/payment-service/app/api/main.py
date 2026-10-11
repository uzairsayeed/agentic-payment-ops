# FastAPI
#     ↓
# defines the web application/routes

# Uvicorn
#     ↓
# ASGI server that actually runs it

from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    Request,
)

from fastapi.responses import JSONResponse

from app.bootstrap import (
    build_payment_application_service,
)

from app.application.payment_service import (
    PaymentApplicationService,
    PaymentNotFoundError,
)
from app.domain.payment import (
    InvalidPaymentData,
    InvalidPaymentTransition,
    Payment
)

app = FastAPI(
    title="Payment Operations Service",
)

# Dependency injection : route needs a PaymentApplicationService, and production and tests should be able to supply different implementations/configurations.
def get_payment_service(
) -> PaymentApplicationService:
    return build_payment_application_service()

# Depends(get_payment_service) means:
    # Before calling this route, FastAPI should obtain the route's PaymentApplicationService by calling get_payment_service().
    # This is FastAPI-level dependency injection.
# Dependency Injection (Present in this file): route doesn't construct what it needs itself.
# Dependency Override (Present in test_payments_api.py): test replaces how that dependency is provided.
PaymentServiceDependency = Annotated[
    PaymentApplicationService,
    Depends(get_payment_service),
]

class CreatePaymentRequest(BaseModel):
    beneficiary_id: str
    source_currency: str
    destination_currency: str
    amount: Decimal

class PaymentResponse(BaseModel):
    payment_id: str
    beneficiary_id: str
    source_currency: str
    destination_currency: str
    amount: Decimal
    status: str

class ErrorResponse(BaseModel):
    error: str
    message: str

def to_payment_response(
    payment: Payment,
) -> PaymentResponse:
    return PaymentResponse(
        payment_id=payment.payment_id,
        beneficiary_id=payment.beneficiary_id,
        source_currency=payment.source_currency,
        destination_currency=payment.destination_currency,
        amount=payment.amount,
        status=payment.status.value,
    )

# Anywhere in this FastAPI application, this domain failure maps this way.
@app.exception_handler(InvalidPaymentData)
async def handle_invalid_payment_data(
    request: Request,
    exc: InvalidPaymentData,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": "INVALID_PAYMENT_DATA",
            "message": str(exc),
        },
    )

@app.exception_handler(PaymentNotFoundError)
async def handle_payment_not_found(
    request: Request,
    exc: PaymentNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": "PAYMENT_NOT_FOUND",
            "message": str(exc),
        },
    )

@app.exception_handler(InvalidPaymentTransition)
async def handle_invalid_payment_transition(
    request: Request,
    exc: InvalidPaymentTransition,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": "INVALID_PAYMENT_TRANSITION",
            "message": str(exc),
        },
    )


@app.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=201,
)
def create_payment(
    request: CreatePaymentRequest,
    payment_service: PaymentServiceDependency,
) -> PaymentResponse:
    payment = payment_service.create_payment(
        beneficiary_id=request.beneficiary_id,
        source_currency=request.source_currency,
        destination_currency=request.destination_currency,
        amount=request.amount,
    )

    return to_payment_response(payment)

@app.get(
    "/payments/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: str,
    payment_service: PaymentServiceDependency,
) -> PaymentResponse:
    payment = payment_service.get_payment(
        payment_id
    )

    return to_payment_response(payment)

# POST /payments/{id}/compliance
#             ↓
# PaymentApplicationService.start_compliance()
#             ↓
# uow.payments.get()
#             ↓
# Payment.transition_to(
#     COMPLIANCE_PENDING
# )
#             ↓
# uow.payments.save()
#             ↓
# uow.commit()
#             ↓
# 200
@app.post(
    "/payments/{payment_id}/compliance",
    response_model=PaymentResponse,
)
def start_compliance(
    payment_id: str,
    payment_service: PaymentServiceDependency,
) -> PaymentResponse:
    payment = payment_service.start_compliance(
        payment_id
    )

    return to_payment_response(payment)