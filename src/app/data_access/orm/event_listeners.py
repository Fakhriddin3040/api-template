"""Mapper-level listeners that stamp audit columns.

Doing it here rather than in every repository means a new model gets `created_at`
/ `created_by_id` for free the moment it inherits the right mixin.
"""

import logging
from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from sqlalchemy import event

from src.app.data_access.orm.base.base_orm_models import SqlAlchemyBaseModel
from src.app.shared_kernel.ports.services import ClockProto

if TYPE_CHECKING:
    # Import-time only: this module is pulled in during `data_access.orm`
    # package init; importing the provider eagerly forms a circular import
    # (execution_context_provider -> user_orm_model -> orm.__init__ ->
    # event_listeners). It is used solely as a type annotation below; the value
    # is supplied at call time via ``Provide["core.execution_context_provider"]``.
    from src.app.shared_kernel.providers.execution_context_provider import (
        ExecutionContextProvider,
    )

logger = logging.getLogger(__name__)


def _current_user_id(ex_ctx_provider: "ExecutionContextProvider"):
    """The acting user, or None outside a request.

    Migrations, CLI seeds and background jobs run with no execution context;
    raising there would make an audit column mandatory in places where no user
    exists.
    """
    try:
        return ex_ctx_provider.get_context().user_id
    except LookupError:
        return None


@event.listens_for(SqlAlchemyBaseModel, "before_insert", propagate=True)
@inject
def set_created_props(
    mapper,
    connection,
    target,
    clock: ClockProto = Provide["core.services.clock"],
    ex_ctx_provider: "ExecutionContextProvider" = Provide[
        "core.execution_context_provider"
    ],
) -> None:
    if hasattr(target, "created_at"):
        target.created_at = clock.get_now()
    if hasattr(target, "created_by_id") and target.created_by_id is None:
        target.created_by_id = _current_user_id(ex_ctx_provider)


@event.listens_for(SqlAlchemyBaseModel, "before_update", propagate=True)
@inject
def set_updated_props(
    mapper,
    connection,
    target,
    clock: ClockProto = Provide["core.services.clock"],
    ex_ctx_provider: "ExecutionContextProvider" = Provide[
        "core.execution_context_provider"
    ],
) -> None:
    if hasattr(target, "updated_at"):
        target.updated_at = clock.get_now()
    if hasattr(target, "updated_by_id") and target.updated_by_id is None:
        target.updated_by_id = _current_user_id(ex_ctx_provider)
