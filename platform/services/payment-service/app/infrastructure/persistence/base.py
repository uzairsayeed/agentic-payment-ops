# What is Base?
# Think of it as SQLAlchemy's registry/root for our persistence models.
# Classes that inherit from it become SQLAlchemy-mapped classes.

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass