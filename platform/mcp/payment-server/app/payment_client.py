from decimal import Decimal

from pydantic import BaseModel

import httpx2
from pydantic import ValidationError

class PaymentView(BaseModel):
    payment_id: str
    beneficiary_id: str
    source_currency: str
    destination_currency: str
    amount: Decimal
    status: str

class PaymentServiceClientError(Exception):
    pass

# downstream Payment Service explicitly said payment does not exist
class PaymentServiceNotFoundError(
    PaymentServiceClientError
):
    pass

# couldn't reliably communicate with Payment Service
class PaymentServiceUnavailableError(
    PaymentServiceClientError
):
    pass

# Payment Service responded, but response violated expected contract
class PaymentServiceInvalidResponseError(
    PaymentServiceClientError
):
    pass

class PaymentServiceClient:
    # why inject AsyncClient?
        # If we use it without injecting, then that would create a new HTTP client on every tool invocation. 
    def __init__(
        self,
        base_url: str,
        http_client: httpx2.AsyncClient,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client

    async def get_payment(
        self,
        payment_id: str,
    ) -> PaymentView:
        try:
            response = await self._http_client.get(
                f"{self._base_url}/payments/{payment_id}"
            )
        except (
            httpx2.ConnectError,
            httpx2.TimeoutException,
        ) as exc:
            raise PaymentServiceUnavailableError(
                "Payment Service is unavailable."
            ) from exc

        if response.status_code == 404:
            raise PaymentServiceNotFoundError(
                f"Payment {payment_id} does not exist."
            )

        if response.status_code >= 400:
            raise PaymentServiceClientError(
                "Payment Service request failed "
                f"with status {response.status_code}."
            )

        try:
            return PaymentView.model_validate(
                response.json()
            )
        except (
            ValueError,
            ValidationError,
        ) as exc:
            raise PaymentServiceInvalidResponseError(
                "Payment Service returned an invalid response."
            ) from exc