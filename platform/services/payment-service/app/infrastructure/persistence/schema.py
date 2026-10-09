from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.database import engine

# Important:
# importing the models registers them with Base.metadata.
from app.infrastructure.persistence import models  # noqa: F401


def create_schema() -> None:
    # Means: Look at all tables registered in this metadata, connect using this engine, and create any that don't already exist.
    # Base.metadata

    # payments
    # payment_events
    #     │
    #     ▼
    # create_all(engine)
    #     │
    #     ▼
    # PostgreSQL
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    create_schema()