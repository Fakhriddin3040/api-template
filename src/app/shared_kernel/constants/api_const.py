from decimal import Decimal

import regex

DEFAULT_LIMIT = 10
DEFAULT_OFFSET = 0

MAX_LIMIT = 300
MIN_LIMIT = 1
MIN_OFFSET = 0

TITLE_MIN_LENGTH = 1
TITLE_MAX_LENGTH = 150

TITLE_REGEX = regex.compile(r"^[\p{L}\p{N} .,:_+/-]+$")


ID_MAX = 2**31 - 1  # 32 bits
PRICE_MAX = Decimal("9_999_999_999")
DECIMAL_ZERO = Decimal("0.00")
PRICE_GT = DECIMAL_ZERO
