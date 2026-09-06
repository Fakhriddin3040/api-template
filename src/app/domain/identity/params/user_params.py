from typing import Optional

from src.app.domain.identity.params.annotated import (
    ATAddress,
    ATDescription,
    ATInformation,
    ATPhone,
    ATUserEmail,
    ATUserName,
)
from src.app.shared_kernel.params.domain_params import DomainParams
from src.app.shared_kernel.types.base_types import ID_T


class UserCreateParams(DomainParams):
    """What a caller supplies to bring a user into existence.

    Account state (`is_active`, `email_confirmed`, `status`, timestamps) is
    deliberately absent: the aggregate decides those, and which factory was used
    is what decides them — see `UserAggregate.register` vs `.create`.
    """

    email: ATUserEmail
    first_name: ATUserName
    last_name: ATUserName
    phone: Optional[ATPhone] = None
    address: Optional[ATAddress] = None
    description: Optional[ATDescription] = None
    information: Optional[ATInformation] = None
    avatar_id: Optional[ID_T] = None


class UserUpdateParams(DomainParams):
    """Editable profile fields.

    Email is absent on purpose: changing the login credential has to go through
    a confirmation flow, not a profile edit.
    """

    first_name: ATUserName
    last_name: ATUserName
    phone: Optional[ATPhone] = None
    address: Optional[ATAddress] = None
    description: Optional[ATDescription] = None
    information: Optional[ATInformation] = None
    avatar_id: Optional[ID_T] = None
