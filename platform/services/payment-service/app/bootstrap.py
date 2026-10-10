# Architecture: This file is intentionally allowed to know both sides:
#               bootstrap.py
#               /          \
#              /            \
#             ▼              ▼
# Application contract    Infrastructure
#                          implementation
from app.application.payment_service import (
    PaymentApplicationService,
)
from app.infrastructure.persistence.unit_of_work import (
    SqlAlchemyUnitOfWork,
)


def build_payment_application_service(
) -> PaymentApplicationService:
    return PaymentApplicationService(
        unit_of_work_factory=SqlAlchemyUnitOfWork,
    )