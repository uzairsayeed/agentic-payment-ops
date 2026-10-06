# Purpose of this file is to encode : What may happen
# What are we doing in this file?
    # 1. Define possible states
    # 2. Define domain-specific error
    # 3. Define transition rules
    # 4. Define function that enforces those rules
    # 5. Define the payment entity
    # 6. Define creation rules

# payment.py
# ├── Payment
# ├── PaymentStatus
# ├── PaymentEvent
# ├── InvalidPaymentTransition
# └── transition rules

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

# Why StrEnum?
    # StrEnum gives us string-like enum values.
    # For example:
        # PaymentStatus.CREATED.value gives CREATED
from enum import StrEnum

class PaymentStatus(StrEnum):
    CREATED = "CREATED"
    COMPLIANCE_PENDING = "COMPLIANCE_PENDING"
    COMPLIANCE_PASSED = "COMPLIANCE_PASSED"
    REJECTED = "REJECTED"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# Add a domain-specific error
# Why not just throw: ValueError everywhere?
    # Because this domain specific error has meaning.
    # It tells : The request was syntactically understandable, but it violated a payment-domain rule.
    # Later different layers can translate it differently.
    # For example:
        # Domain
        #     ↓
        # InvalidPaymentTransition
        # The above might eventually become:
        # FastAPI
        #     ↓
        # HTTP 409 Conflict
class InvalidPaymentTransition(ValueError):
    pass

ALLOWED_TRANSITIONS: dict[
    PaymentStatus,
    set[PaymentStatus],
] = {
    PaymentStatus.CREATED: {
        PaymentStatus.COMPLIANCE_PENDING,
    },

    PaymentStatus.COMPLIANCE_PENDING: {
        PaymentStatus.COMPLIANCE_PASSED,
        PaymentStatus.REJECTED,
    },

    PaymentStatus.COMPLIANCE_PASSED: {
        PaymentStatus.SUBMITTED,
    },

    PaymentStatus.SUBMITTED: {
        PaymentStatus.PROCESSING,
        PaymentStatus.FAILED,
    },

    PaymentStatus.PROCESSING: {
        PaymentStatus.COMPLETED,
        PaymentStatus.FAILED,
    },

    # Why are terminal states empty sets?
        # That means: no valid next state
    PaymentStatus.REJECTED: set(),
    PaymentStatus.COMPLETED: set(),
    PaymentStatus.FAILED: set(),
}

# Why a function instead of scattering checks everywhere?
    # Bad approach:
        # if payment.status == "CREATED":
            # ...
        # This will be added inside the business logic of an API endpoint then another worker does the same and the MCP might eventually does another version
    # Instead: One deterministic source of truth.
        #         validate_transition()
        #                ▲
        #     ┌──────────┼──────────┐
        #     │          │          │
        # HTTP       Worker        MCP
def validate_transition(
    current_status: PaymentStatus,
    new_status: PaymentStatus,
) -> None:

    allowed = ALLOWED_TRANSITIONS[current_status]

    if new_status not in allowed:
        raise InvalidPaymentTransition(
            f"Cannot transition payment "
            f"from {current_status} to {new_status}."
        )

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# frozen=True : makes the event immutable after creation.
@dataclass(frozen=True)
class PaymentEvent:
    event_type: str
    from_status: PaymentStatus | None
    to_status: PaymentStatus
    occurred_at: datetime

# Define the payment entity
# What does @dataclass do?
    # @dataclass generates much of that repetitive Python plumbing for us like creating constructor
    # Python automatically generates a standard __init__() method to assign your type-hinted fields to the instance.
    # It does not make this a database model.
    # It does not come from SQLAlchemy.
    # It is just standard Python.
# @dataclass
# class Payment:
#     beneficiary_id: str
#     source_currency: str
#     destination_currency: str
#     amount: Decimal

#     # init=False?
#         # That means callers don't provide it, instead the domain will generate it.
#     payment_id: str = field(init=False)
#     status: PaymentStatus = field(init=False)

#     created_at: datetime = field(init=False)
#     updated_at: datetime = field(init=False)

#     events: list[PaymentEvent] = field(
#         init=False,
#         # Each Payment gets its own list.
#         # events = [] <-> We don't want different payment instances accidentally sharing the same mutable list.
#         default_factory=list,
#     )

#     # Add creation rules with __post_init__
#     # __post_init__() is a dataclass hook.
#     # When you decorate a class with @dataclass, 
#     # Python automatically generates a standard __init__() method to assign your type-hinted fields to the instance. 
#     # Because overriding __init__() directly would defeat the purpose of using a dataclass, 
#     # Python provides __post_init__() as a dedicated hook that automatically executes immediately after the generated __init__() finishes.
#     def __post_init__(self) -> None:
#         if self.amount <= 0:
#             raise ValueError(
#                 "Payment amount must be greater than zero."
#             )

#         self.source_currency = self.source_currency.upper()
#         self.destination_currency = (
#             self.destination_currency.upper()
#         )

#         if len(self.source_currency) != 3:
#             raise ValueError(
#                 "Source currency must be a 3-letter code."
#             )

#         if len(self.destination_currency) != 3:
#             raise ValueError(
#                 "Destination currency must be a 3-letter code."
#             )

#         now = utc_now()

#         self.payment_id = (
#             f"PAY-{uuid4().hex.upper()}"
#         )

#         self.status = PaymentStatus.CREATED

#         self.created_at = now
#         self.updated_at = now

#         self.events.append(
#             PaymentEvent(
#                 event_type="PAYMENT_CREATED",
#                 from_status=None,
#                 to_status=PaymentStatus.CREATED,
#                 occurred_at=now,
#             )
#         )



@dataclass
class Payment:
    payment_id: str
    beneficiary_id: str
    source_currency: str
    destination_currency: str
    amount: Decimal
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    events: list[PaymentEvent] = field(
        default_factory=list
    )

    @classmethod
    def create(
        cls,
        *,
        beneficiary_id: str,
        source_currency: str,
        destination_currency: str,
        amount: Decimal,
    ) -> "Payment":
        if amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        source_currency = source_currency.upper()
        destination_currency = destination_currency.upper()

        if len(source_currency) != 3:
            raise ValueError(
                "Source currency must be a 3-letter code."
            )

        if len(destination_currency) != 3:
            raise ValueError(
                "Destination currency must be a 3-letter code."
            )

        now = utc_now()

        payment = cls(
            payment_id=f"PAY-{uuid4().hex.upper()}",
            beneficiary_id=beneficiary_id,
            source_currency=source_currency,
            destination_currency=destination_currency,
            amount=amount,
            status=PaymentStatus.CREATED,
            created_at=now,
            updated_at=now,
        )

        payment.events.append(
            PaymentEvent(
                event_type="PAYMENT_CREATED",
                from_status=None,
                to_status=PaymentStatus.CREATED,
                occurred_at=now,
            )
        )

        return payment

    @classmethod
    def restore(
        cls,
        *,
        payment_id: str,
        beneficiary_id: str,
        source_currency: str,
        destination_currency: str,
        amount: Decimal,
        status: PaymentStatus,
        created_at: datetime,
        updated_at: datetime,
        events: list[PaymentEvent],
    ) -> "Payment":
        return cls(
            payment_id=payment_id,
            beneficiary_id=beneficiary_id,
            source_currency=source_currency,
            destination_currency=destination_currency,
            amount=amount,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            events=events,
        )

    def transition_to(
        self,
        new_status: PaymentStatus,
        *,
        event_type: str,
    ) -> None:
        validate_transition(
            self.status,
            new_status,
        )

        previous_status = self.status
        now = utc_now()

        self.status = new_status
        self.updated_at = now

        self.events.append(
            PaymentEvent(
                event_type=event_type,
                from_status=previous_status,
                to_status=new_status,
                occurred_at=now,
            )
        )