from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional, Tuple, TypeAlias, List

from src.app.shared_kernel.types.base_types import ID_T
from pydantic import AfterValidator, Field, constr, StringConstraints
from pydantic.functional_validators import BeforeValidator
from src.app.shared_kernel.constants import common_constraints as common_constraints
from src.app.shared_kernel.constants.common_constraints import (
    COMMENT_MAX_LENGTH,
    DATETIME_MAX,
    MIN_RATE,
    MAX_RATE,
)
from src.app.modules.filtering.types import FilterSpec
from src.app.shared_kernel.utils.functions.common_funcs import (
    set_timezone,
    parse_single_line_str,
    default_utc_now,
)

# ===== Str =====
type ATSingleLineStr = Annotated[str, BeforeValidator(parse_single_line_str)]

type ATInformationStr = Annotated[
    str, constr(max_length=common_constraints.INFORMATION_MAX_LENGTH)
]

type ATComment = Annotated[str, constr(max_length=COMMENT_MAX_LENGTH)]


# ===== Decimal =====
type ATPrice = Annotated[
    Decimal,
    Field(
        max_digits=common_constraints.DECIMAL_PRICE_DIGITS,
        decimal_places=common_constraints.DECIMAL_PRICE_PLACES,
    ),
]
type ATDiscount = Annotated[
    Decimal,
    Field(
        max_digits=common_constraints.DECIMAL_DISCOUNT_DIGITS,
        decimal_places=common_constraints.DECIMAL_DISCOUNT_PLACES,
        ge=Decimal("-0.99"),
        le=Decimal("100"),
    ),
]
ATBalance: TypeAlias = Annotated[
    Decimal,
    Field(
        max_digits=common_constraints.DECIMAL_BALANCE_DIGITS,
        decimal_places=common_constraints.DECIMAL_BALANCE_PLACES,
    ),
]

type ATRate = Annotated[Decimal, Field(gt=MIN_RATE, le=MAX_RATE)]

# ===== HTTP =====
type ATDomainName = Annotated[
    str,
    StringConstraints(
        max_length=253,
        min_length=4,
        pattern=r"^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}$",
        strip_whitespace=True,
    ),
    lambda x: x[:-1] if x[-1] == "/" else x,
]

type ATFileIds = Annotated[
    List[ID_T], Field(max_length=common_constraints.FILE_IDS_MAX_COUNT)
]

# ====== Date =======
type ATDatetime = Annotated[datetime, AfterValidator(set_timezone)]
type ATDatetimeDefault = Annotated[
    datetime, BeforeValidator(default_utc_now), AfterValidator(set_timezone)
]


ATDatetimeRN = Annotated[
    Tuple[Optional[ATDatetime], Optional[ATDatetime]],
    FilterSpec.datetime_range(
        lte=DATETIME_MAX,
    ),
]
