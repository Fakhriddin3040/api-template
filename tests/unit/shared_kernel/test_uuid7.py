import time
from uuid import UUID

import pytest

from src.app.shared_kernel.utils.functions.uuid_funcs import uuid7

pytestmark = [pytest.mark.unit, pytest.mark.shared_kernel]


class TestUuid7:
    def test_is_a_version_7_uuid(self):
        value = uuid7()

        assert isinstance(value, UUID)
        assert value.version == 7

    def test_is_time_ordered(self):
        """The property the whole choice rests on: ids sort by creation time,
        so they index like a sequence instead of scattering across the B-tree."""
        first = uuid7()
        time.sleep(0.005)
        second = uuid7()

        assert first < second

    def test_values_are_unique(self):
        assert len({uuid7() for _ in range(1000)}) == 1000


class TestEveryIdIsUuid7:
    """Every id the template generates — row, event, trace — is a v7."""

    def test_orm_primary_key_defaults_to_uuid7_on_both_sides(self):
        from src.app.data_access.orm.models import UserOrmModel

        column = UserOrmModel.__table__.c.id
        assert column.default.arg.__name__ == "uuid7"
        # Raw-SQL inserts that bypass the ORM get one from Postgres 18.
        assert str(column.server_default.arg) == "uuidv7()"

    def test_event_id_is_uuid7(self):
        from src.app.shared_kernel.types.event_types import BaseEvent

        assert BaseEvent().event_id.version == 7

    def test_trace_id_is_uuid7(self):
        from src.app.shared_kernel.types.execution_context import ExecutionContext

        assert ExecutionContext().trace_id.version == 7
