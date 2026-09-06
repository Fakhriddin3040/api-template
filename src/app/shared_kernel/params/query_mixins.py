from typing import Set, Optional, Self

from pydantic import model_validator

from src.app.shared_kernel.params.ordering import OrderingContainer


class OrderingQueryMixin:
    ordering: Optional[OrderingContainer] = None

    _ordering_allowed_fields: Set[str]

    @model_validator(mode="after")
    def validate_ordering(self) -> Self:
        if self.ordering and self.ordering.items:
            given_fields = set(item.field for item in self.ordering.items)
            unexpected_fields = given_fields - self._ordering_allowed_fields

            if unexpected_fields:
                raise ValueError(
                    f"Unexpected fields for ordering: {', '.join(unexpected_fields)}"
                )

        return self

    @classmethod
    def get_allowed_fields(cls) -> Set[str]:
        return (
            cls._ordering_allowed_fields
            if isinstance(cls._ordering_allowed_fields, set)
            else set()
        )
