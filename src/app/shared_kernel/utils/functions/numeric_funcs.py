from decimal import ROUND_HALF_UP, Decimal
from typing import Tuple

from src.app.shared_kernel.types.base_types import Numeric

_CENTS = Decimal("0.01")


def split_amount(number: Numeric) -> Tuple[int, int]:
    """Split an amount into (whole, hundredths).

    Rounds to 2 decimals FIRST, then splits. Splitting first would report
    ``1234.999`` as ``1234`` and ``0`` — the rounding of the fraction up to 100
    has to carry into the whole part, not vanish.
    """
    value = Decimal(str(number)).quantize(_CENTS, rounding=ROUND_HALF_UP)
    whole = int(value)  # truncates toward zero, so the sign lives here
    fractional = int((abs(value - whole) * 100).to_integral_value())
    return whole, fractional


def quantize_money(number: Numeric) -> Decimal:
    """Round to 2 decimals, half-up — the rounding a human expects on money."""
    return Decimal(str(number)).quantize(_CENTS, rounding=ROUND_HALF_UP)
