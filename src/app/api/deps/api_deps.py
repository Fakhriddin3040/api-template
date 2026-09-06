from dependency_injector.wiring import Provide, inject

from src.app.shared_kernel.ports.mediator import MediatorProto


@inject
def _mediator(mediator=Provide["infra.mediator"]) -> MediatorProto:
    return mediator


async def get_mediator() -> MediatorProto:
    return _mediator()
