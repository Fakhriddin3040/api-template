from typing import Callable

from dependency_injector.wiring import Provide, inject

from src.app.application.identity.commands.auth_commands import (
    ConfirmEmailCommand,
    LoginCommand,
    RefreshTokenCommand,
    RegisterCommand,
    ResendEmailConfirmationCommand,
)
from src.app.application.identity.commands.forgot_commands import (
    ForgotPasswordStep1Command,
    ForgotPasswordStep2Command,
    ForgotPasswordStep3Command,
)
from src.app.application.identity.commands.user_commands import (
    ChangePasswordCommand,
    UserToggleStatusCommand,
    UserUpdateMeCommand,
)
from src.app.application.identity.queries.user_queries import (
    MeQuery,
    UserDetailedQuery,
    UserListQuery,
)
from src.app.shared_kernel.ports.mediator import MediatorProto


@inject
def _register_handlers(
    mediator: MediatorProto = Provide["infra.mediator"],
    register: Callable = Provide["identity.command_handlers.register_handler"],
    confirm_email: Callable = Provide["identity.command_handlers.confirm_email_handler"],
    resend_confirmation: Callable = Provide[
        "identity.command_handlers.resend_confirmation_handler"
    ],
    login: Callable = Provide["identity.command_handlers.login_handler"],
    refresh_token: Callable = Provide["identity.command_handlers.refresh_token_handler"],
    forgot_step1: Callable = Provide["identity.command_handlers.forgot_step1_handler"],
    forgot_step2: Callable = Provide["identity.command_handlers.forgot_step2_handler"],
    forgot_step3: Callable = Provide["identity.command_handlers.forgot_step3_handler"],
    update_me: Callable = Provide["identity.command_handlers.update_me_handler"],
    change_password: Callable = Provide[
        "identity.command_handlers.change_password_handler"
    ],
    toggle_status: Callable = Provide[
        "identity.command_handlers.user_toggle_status_handler"
    ],
    me: Callable = Provide["identity.query_handlers.me_handler"],
    user_detailed: Callable = Provide["identity.query_handlers.user_detailed_handler"],
    user_list: Callable = Provide["identity.query_handlers.user_list_handler"],
) -> None:
    mediator.register_command(RegisterCommand, register)
    mediator.register_command(ConfirmEmailCommand, confirm_email)
    mediator.register_command(ResendEmailConfirmationCommand, resend_confirmation)
    mediator.register_command(LoginCommand, login)
    mediator.register_command(RefreshTokenCommand, refresh_token)

    mediator.register_command(ForgotPasswordStep1Command, forgot_step1)
    mediator.register_command(ForgotPasswordStep2Command, forgot_step2)
    mediator.register_command(ForgotPasswordStep3Command, forgot_step3)

    mediator.register_command(UserUpdateMeCommand, update_me)
    mediator.register_command(ChangePasswordCommand, change_password)
    mediator.register_command(UserToggleStatusCommand, toggle_status)

    mediator.register_query(MeQuery, me)
    mediator.register_query(UserDetailedQuery, user_detailed)
    mediator.register_query(UserListQuery, user_list)


def setup() -> None:
    _register_handlers()
