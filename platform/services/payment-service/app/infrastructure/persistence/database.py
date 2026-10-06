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