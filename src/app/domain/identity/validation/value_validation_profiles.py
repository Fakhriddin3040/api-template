import datetime
from uuid import UUID

from src.app.domain.identity.identity_constraints import (
    USER_ADDRESS_MAX_LENGTH,
    USER_DESCRIPTION_MAX_LENGTH,
    USER_EMAIL_MAX_LENGTH,
    USER_EMAIL_MIN_LENGTH,
    USER_EMAIL_REGEX,
    USER_NAME_MAX_LENGTH,
    USER_NAME_MIN_LENGTH,
    USER_NAME_REGEX,
    USER_PHONE_MAX_LENGTH,
    USER_PHONE_MIN_LENGTH,
    USER_PHONE_REGEX,
)
from src.app.shared_kernel.constants.models_fields.identity_model_fields import (
    UserField,
)
from src.app.shared_kernel.validation.value_validation.value_validation_schema import (
    ValueValidationProfile,
    StrFieldValueValidationSpecFactory,
    ObjectFieldValidationSpecFactory,
)

_NAME_FIELDS = (UserField.FIRST_NAME, UserField.LAST_NAME)

UserCreateValueValidationProfile = ValueValidationProfile(
    fields=[
        StrFieldValueValidationSpecFactory(
            field=UserField.EMAIL,
            required=True,
            max_length=USER_EMAIL_MAX_LENGTH,
            min_length=USER_EMAIL_MIN_LENGTH,
            re_pattern=USER_EMAIL_REGEX,
        ),
        *[
            StrFieldValueValidationSpecFactory(
                field=field,
                required=True,
                min_length=USER_NAME_MIN_LENGTH,
                max_length=USER_NAME_MAX_LENGTH,
                re_pattern=USER_NAME_REGEX,
            )
            for field in _NAME_FIELDS
        ],
        StrFieldValueValidationSpecFactory(
            field=UserField.PHONE,
            required=False,
            max_length=USER_PHONE_MAX_LENGTH,
            min_length=USER_PHONE_MIN_LENGTH,
            re_pattern=USER_PHONE_REGEX,
        ),
        StrFieldValueValidationSpecFactory(
            field=UserField.ADDRESS,
            required=False,
            max_length=USER_ADDRESS_MAX_LENGTH,
        ),
        StrFieldValueValidationSpecFactory(
            field=UserField.DESCRIPTION,
            required=False,
            max_length=USER_DESCRIPTION_MAX_LENGTH,
        ),
        StrFieldValueValidationSpecFactory(
            field=UserField.INFORMATION,
            required=False,
        ),
        ObjectFieldValidationSpecFactory(
            field=UserField.AVATAR_ID, required=False, instance_of=UUID
        ),
        ObjectFieldValidationSpecFactory(
            field=UserField.EMAIL_CONFIRMED, required=True, instance_of=bool
        ),
        ObjectFieldValidationSpecFactory(
            field=UserField.LAST_LOGIN_TIME, required=False, instance_of=datetime
        ),
    ]
)

UserUpdateValueValidationProfile = ValueValidationProfile(
    fields=[
        *[
            StrFieldValueValidationSpecFactory(
                field=field,
                required=False,
                min_length=USER_NAME_MIN_LENGTH,
                max_length=USER_NAME_MAX_LENGTH,
                re_pattern=USER_NAME_REGEX,
            )
            for field in _NAME_FIELDS
        ],
        StrFieldValueValidationSpecFactory(
            field=UserField.PHONE,
            required=False,
            max_length=USER_PHONE_MAX_LENGTH,
            min_length=USER_PHONE_MIN_LENGTH,
            re_pattern=USER_PHONE_REGEX,
        ),
        StrFieldValueValidationSpecFactory(
            field=UserField.ADDRESS,
            required=False,
            max_length=USER_ADDRESS_MAX_LENGTH,
        ),
        StrFieldValueValidationSpecFactory(
            field=UserField.DESCRIPTION,
            required=False,
            max_length=USER_DESCRIPTION_MAX_LENGTH,
        ),
        StrFieldValueValidationSpecFactory(
            field=UserField.INFORMATION,
            required=False,
        ),
        ObjectFieldValidationSpecFactory(
            field=UserField.AVATAR_ID, required=False, instance_of=UUID
        ),
    ]
)
