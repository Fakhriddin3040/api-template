from dependency_injector.wiring import Provide, inject

from src.app.domain.identity.events import (
    ForgotPasswordStep1Event,
    ForgotPasswordStep2Event,
    UserEmailConfirmedEvent,
    UserRegisteredEvent,
)
from src.app.shared_kernel.ports.event import EventBusProto


@inject
def setup(
    bus: EventBusProto = Provide["infra.event_bus"],
    user_registered=Provide["infra.event_handlers.user_registered_event_handler"],
    forgot_step1=Provide["infra.event_handlers.forgot_password_step1_event_handler"],
    forgot_step2=Provide["infra.event_handlers.forgot_password_step2_event_handler"],
    email_confirmed=Provide["identity.event_handlers.user_email_confirmed_handler"],
) -> None:
    bus.subscribe(UserRegisteredEvent, user_registered)
    bus.subscribe(ForgotPasswordStep1Event, forgot_step1)
    bus.subscribe(ForgotPasswordStep2Event, forgot_step2)
    bus.subscribe(UserEmailConfirmedEvent, email_confirmed)
