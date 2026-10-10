# FastAPI
#     ↓
# defines the web application/routes

# Uvicorn
#     ↓
# ASGI server that actually runs it

from decimal import Decimal

from fastapi import FastAPI
from pydantic import BaseModel

from app.bootstrap import (
    build_payment_application_service,
)

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

app = FastAPI(
    title="Payment Operations Service",
)

payment_service = build_payment_application_service()

@app.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=201,
)
def create_payment(
    request: CreatePaymentRequest,
) -> PaymentResponse:
    payment = payment_service.create_payment(
        beneficiary_id=request.beneficiary_id,
        source_currency=request.source_currency,
        destination_currency=request.destination_currency,
        amount=request.amount,
    )

    return PaymentResponse(
        payment_id=payment.payment_id,
        beneficiary_id=payment.beneficiary_id,
        source_currency=payment.source_currency,
        destination_currency=payment.destination_currency,
        amount=payment.amount,
        status=payment.status.value,
    )