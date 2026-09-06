from typing import Annotated

from src.app.shared_kernel.constants.common_enums import StatusEnum
from src.app.modules.filtering.types import FilterSpec

AFStatus = Annotated[StatusEnum, FilterSpec.enum(StatusEnum)]
