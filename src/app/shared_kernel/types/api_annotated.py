from typing import Annotated

from pydantic import StringConstraints

from src.app.modules.filtering.meta import FilterSpec

type AFSearch = Annotated[ATSearch, FilterSpec.string()]


ATSearch = Annotated[
    str,
    StringConstraints(
        max_length=100,
        strip_whitespace=True,
    ),
]
