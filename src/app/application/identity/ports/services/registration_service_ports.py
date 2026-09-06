from typing import Protocol, runtime_checkable

from src.app.application.identity.commands.auth_commands import RegisterCommand
from src.app.domain.identity.aggregates.user_aggregate import UserAggregate
from src.app.shared_kernel.ports.result import ResultDetailed


@runtime_checkable
class UserRegistrationServiceProto(Protocol):
    async def register(self, cmd: RegisterCommand) -> ResultDetailed[UserAggregate]:
        """Build the (inactive) user, hash the password and persist it.

        Leaves the transaction to the caller; the returned aggregate is already
        flushed, so it carries its id.
        """


@runtime_checkable
class ForgotPasswordServiceProto(Protocol):
    async def issue_reset_code(self, user_aggr: UserAggregate) -> ResultDetailed[None]:
        """Mint a reset code for the user and raise the "code issued" event."""

    def announce_password_changed(
        self, user_aggr: UserAggregate, new_password: str
    ) -> None: ...
