# Our repository
#       ↓
# SQLAlchemy
#       ↓
# psycopg
#       ↓
# TCP
#       ↓
# PostgreSQL

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# means:
    # postgresql+psycopg
            # ↓
    # SQLAlchemy dialect + driver

    # payment_user
    #         ↓
    # username

    # payment_password
    #         ↓
    # password

    # localhost
    #         ↓
    # database host

    # 5432
    #         ↓
    # PostgreSQL port

    # payment_ops
    #         ↓
    # database name
DATABASE_URL = (
    "postgresql+psycopg://"
    "payment_user:"
    "payment_password@"
    "localhost:55432/"
    "payment_ops"
)


engine = create_engine(
    DATABASE_URL,
)

# engine
#    ↓
# SessionFactory
#    ↓
# Session instance
# Think of a Session as a unit of database work.

# Why a factory?
# We don't want one global Session reused forever
# Instead:
    # Use case A
    # ↓
    # Session A

    # Use case B
    # ↓
    # Session B
SessionFactory = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)