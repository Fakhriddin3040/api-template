from typing import Optional

from src.app.domain.identity.params.annotated import (
    ATAddress,
    ATPassword,
    ATPhone,
    ATUserName,
)
from src.app.shared_kernel.pydantic.types import Command
from src.app.shared_kernel.types.base_types import ID_T


class UserUpdateMeCommand(Command):
    """Edit your own profile. Email is deliberately absent — changing the login
    credential has to go through a confirmation flow, not a profile PATCH."""

    first_name: ATUserName
    last_name: ATUserName
    phone: Optional[ATPhone] = None
    address: Optional[ATAddress] = None
    description: Optional[str] = None
    information: Optional[str] = None
    avatar_id: Optional[ID_T] = None


class ChangePasswordCommand(Command):
    old_password: str
    new_password: ATPassword


class UserToggleStatusCommand(Command):
    id: ID_T
