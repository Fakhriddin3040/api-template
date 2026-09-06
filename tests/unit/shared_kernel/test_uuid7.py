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
