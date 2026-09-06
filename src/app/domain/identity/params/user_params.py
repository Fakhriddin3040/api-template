from datetime import datetime
from typing import Optional

from src.app.domain.identity.validation.value_validation_profiles import (
    UserCreateValueValidationProfile,
    UserUpdateValueValidationProfile,
)
from src.app.shared_kernel.params.input_params import DomainInputParams
from src.app.shared_kernel.types.base_types import ID_T
from src.app.utils.decorators.class_decorators import domain_params


@domain_params()
class UserCreateParams(DomainInputParams):
    value_validation_profile = UserCreateValueValidationProfile

    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    address: Optional[str]
    description: Optional[str]
    information: Optional[str]
    avatar_id: Optional[ID_T]
    email_confirmed: bool
    last_login_time: Optional[datetime]


@domain_params()
class UserUpdateParams(DomainInputParams):
    value_validation_profile = UserUpdateValueValidationProfile

    first_name: str
    last_name: str
    phone: Optional[str]
    address: Optional[str]
    description: Optional[str]
    information: Optional[str]
    avatar_id: Optional[ID_T]
