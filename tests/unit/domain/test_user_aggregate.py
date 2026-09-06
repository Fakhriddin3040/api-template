import pytest

from src.app.domain.identity.aggregates.user_aggregate import UserAggregate
from src.app.domain.identity.events import UserRegisteredEvent
from src.app.domain.identity.params.user_params import (
    UserCreateParams,
    UserUpdateParams,
)
from src.app.shared_kernel.constants.common_enums import StatusEnum

pytestmark = [pytest.mark.unit, pytest.mark.domain]


def _params(**overrides) -> UserCreateParams:
    defaults = dict(
        email="someone@example.com",
        first_name="Ada",
        last_name="Lovelace",
    )
    defaults.update(overrides)
    return UserCreateParams(**defaults)


class TestRegister:
    def test_starts_inactive_and_unconfirmed(self, source_factory, clock):
        user = UserAggregate.register(_params(), source_factory, clock)

        assert user.is_active is False
        assert user.email_confirmed is False
        # is_active and status are two views of one fact; they must be seeded
        # together or the account reads as "active but unusable".
        assert user.source.get("status") == StatusEnum.INACTIVE

    def test_confirm_email_activates(self, source_factory, clock):
        user = UserAggregate.register(_params(), source_factory, clock)

        user.confirm_email()

        assert user.email_confirmed is True
        assert user.is_active is True

    def test_mark_registered_emits_the_code(self, source_factory, clock):
        user = UserAggregate.register(_params(), source_factory, clock)

        user.mark_registered("123456")
        events = user.pull_events()

        assert len(events) == 1
        assert isinstance(events[0], UserRegisteredEvent)
        assert events[0].otp_code == "123456"
        assert events[0].recipient == "someone@example.com"


class TestCreate:
    def test_seeded_user_is_usable_immediately(self, source_factory, clock):
        user = UserAggregate.create(_params(), source_factory, clock)

        assert user.is_active is True
        assert user.email_confirmed is True

    def test_the_factory_decides_account_state_not_the_caller(
        self, source_factory, clock
    ):
        """Same params, opposite state — which factory ran is the only input."""
        param = _params()

        registered = UserAggregate.register(param, source_factory, clock)
        created = UserAggregate.create(param, source_factory, clock)

        assert registered.is_active is False
        assert created.is_active is True


class TestUpdate:
    def test_changing_email_unconfirms_it(self, source_factory, clock):
        user = UserAggregate.create(_params(), source_factory, clock)

        user.change_email("other@example.com")

        assert user.email == "other@example.com"
        # The new address is unproven until its own code comes back.
        assert user.email_confirmed is False

    def test_same_email_is_a_no_op(self, source_factory, clock):
        user = UserAggregate.create(_params(), source_factory, clock)

        user.change_email("someone@example.com")

        assert user.email_confirmed is True

    def test_update_writes_profile_fields(self, source_factory, clock):
        user = UserAggregate.create(_params(), source_factory, clock)

        user.update(
            UserUpdateParams(
                first_name="Grace",
                last_name="Hopper",
                address="Arlington",
            )
        )

        assert user.full_name == "Grace Hopper"
        assert user.address == "Arlington"


class TestPassword:
    def test_set_password_stores_a_hash(self, source_factory, clock, password_service):
        user = UserAggregate.create(_params(), source_factory, clock)

        user.set_password("correct horse battery", password_service)

        assert user.password != "correct horse battery"
        assert password_service.verify_password("correct horse battery", user.password)
