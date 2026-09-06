from typing import Protocol, runtime_checkable

from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.shared_kernel.ports.result import ResultDetailed
from src.app.shared_kernel.types.base_types import ID_T


@runtime_checkable
class UserConfirmationServiceProto(Protocol):
    """The one confirmation surface for users.

    Kind-agnostic: every mailed-code confirmation goes through `issue` and
    `confirm`, and adding a kind means adding an enum member and an event — not
    another service.

    Scoped to users by construction; `content_type` is pinned internally so a
    code issued for anything else can never resolve here.
    """

    async def issue(
        self,
        *,
        content_id: ID_T,
        kind: OtpKindEnum,
        target_value: str,
    ) -> ResultDetailed[str]:
        """Mint a fresh numeric OTP and return the code to mail.

        Enforces the per-kind resend cooldown, then burns any still-unused OTP
        for this (user, kind) so only one live code exists at a time.
        """

    async def confirm(
        self,
        *,
        content_id: ID_T,
        otp: str,
        kind: OtpKindEnum,
    ) -> ResultDetailed[ID_T]:
        """Validate and consume a code, then publish the kind's event.

        `content_id` is required, not optional: a six-digit code is not unique on
        its own, so it only identifies a confirmation together with its owner.

        Checks scope, prior use and expiry, consumes atomically, and publishes
        the concrete per-kind event so handlers can apply the side effect.
        Returns the confirmed user's id.
        """
