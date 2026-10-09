from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.payment import PaymentStatus
from app.infrastructure.persistence.base import Base

class PaymentRecord(Base):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(
        String(40),
        primary_key=True,
    )

    beneficiary_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    source_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    destination_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False,
    )

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="ck_payments_status",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_payments_amount_positive",
        ),
    )

class PaymentEventRecord(Base):
    __tablename__ = "payment_events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    payment_id: Mapped[str] = mapped_column(
        ForeignKey("payments.payment_id"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    from_status: Mapped[PaymentStatus | None] = mapped_column(
        Enum(
            PaymentStatus,
            name="ck_payment_events_from_status",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=True,
    )

    to_status: Mapped[PaymentStatus] = mapped_column(
        Enum(
            PaymentStatus,
            name="ck_payment_events_to_status",
            native_enum=False,
            create_constraint=True,
        ),
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )