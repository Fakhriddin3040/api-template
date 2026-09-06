"""Domain params are validated by pydantic at construction.

That is the whole contract: an aggregate never re-checks a field, so anything
that reaches it must have been rejected here first.
"""

import pytest
from pydantic import ValidationError

from src.app.domain.identity.params.user_params import (
    UserCreateParams,
    UserUpdateParams,
)

pytestmark = [pytest.mark.unit, pytest.mark.domain]


def _create(**overrides) -> UserCreateParams:
    defaults = dict(email="someone@example.com", first_name="Ada", last_name="Lovelace")
    defaults.update(overrides)
    return UserCreateParams(**defaults)


class TestValidation:
    @pytest.mark.parametrize(
        "field,value",
        [
            ("email", "not-an-email"),
            ("email", "a@b"),
            ("first_name", ""),
            ("first_name", "Ada123"),
            ("last_name", "!!"),
            ("phone", "12"),
            ("phone", "not-a-phone"),
            ("address", "x" * 501),
        ],
    )
    def test_rejects_bad_values(self, field: str, value: str):
        with pytest.raises(ValidationError):
            _create(**{field: value})

    def test_accepts_a_minimal_valid_set(self):
        param = _create()

        assert param.email == "someone@example.com"
        # Optional fields default rather than being required at every call site.
        assert param.phone is None
        assert param.avatar_id is None

    def test_email_is_normalised_to_lower_case(self):
        """The login is looked up by exact match, so it is normalised on the way
        in rather than lower-cased at every call site."""
        assert _create(email="Someone@Example.COM").email == "someone@example.com"

    def test_names_are_stripped(self):
        assert _create(first_name="  Ada  ").first_name == "Ada"


class TestParamsAreMessages:
    def test_frozen(self):
        param = _create()

        with pytest.raises(ValidationError):
            param.email = "other@example.com"

    def test_unknown_field_is_rejected(self):
        """These are built in our own code, so an unknown key is a typo — and a
        silently ignored one is how a renamed field stops being written."""
        with pytest.raises(ValidationError):
            _create(is_active=True)

    def test_update_params_carry_no_email(self):
        # Changing the login credential must go through a confirmation flow,
        # never a profile edit.
        assert "email" not in UserUpdateParams.model_fields
