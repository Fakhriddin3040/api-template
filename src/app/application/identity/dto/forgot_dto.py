import msgspec

from src.app.shared_kernel.types.base_types import ID_T


class MessageResponseDTO(msgspec.Struct):
    """A human-readable acknowledgement for the step-wise password flows."""

    data: str


class ForgotPasswordStep1ResponseDTO(MessageResponseDTO): ...


class ForgotPasswordStep3ResponseDTO(MessageResponseDTO): ...


class ForgotPasswordStep2ResponseDTO(msgspec.Struct):
    """Who the code belongs to — shown on the "set a new password" screen so the
    user can see which account they are about to change."""

    id: ID_T
    full_name: str
    email: str
    avatar_url: str | None = None
