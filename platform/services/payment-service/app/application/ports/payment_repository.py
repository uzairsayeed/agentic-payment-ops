# Why Protocol?
    # We could use an abstract base class:
        # class PaymentRepository(ABC):
            # @abstractmethod
            # def get(...):
            #     ...
    # and force:
        # class SqlAlchemyPaymentRepository(
        #     PaymentRepository
        # ):

    # That is valid.
    # But Python supports structural typing using Protocol.
    # Meaning: If an object has the methods required by the protocol, it satisfies the contract.

    # Conceptually:
        # PaymentRepository Protocol says:
            # "I require get/add/save"

        # SqlAlchemyPaymentRepository says:
            # "I happen to provide get/add/save"

        # Therefore it can satisfy the contract.
from typing import Protocol

from app.domain.payment import Payment


class PaymentRepository(Protocol):
    def add(
        self,
        payment: Payment,
    ) -> None:
        # ... means : This describes the required shape; implementation lives elsewhere.
        ...

    def get(
        self,
        payment_id: str,
    ) -> Payment | None:
        ...

    def save(
        self,
        payment: Payment,
    ) -> None:
        ...