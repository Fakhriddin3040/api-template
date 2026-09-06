import time
from typing import Any, Dict, Optional
from uuid import uuid4

import jwt

from src.app.shared_kernel.config.infra_configs import JwtConfig
from src.app.shared_kernel.constants.enums import (
    JwtKeys,
    JwtPayload,
    JwtToken,
    JwtType,
)
from src.app.shared_kernel.constants.models_fields.identity_model_fields import (
    UserField,
)
from src.app.shared_kernel.ports.security.jwt_proto import JwtProviderProto


class JwtProvider(JwtProviderProto):
    def __init__(self, config: JwtConfig):
        self.config = config

    def for_user(self, user: Any) -> JwtToken:
        user_payload = self.payload_from_user(user=user)
        access_payload = self.get_payload(
            expire=self.config.access_token_lifetime,
            token_type=JwtType.ACCESS_TOKEN,
            **user_payload,
        )
        refresh_payload = self.get_payload(
            expire=self.config.refresh_token_lifetime,
            token_type=JwtType.REFRESH_TOKEN,
            **user_payload,
        )

        return JwtToken(
            access_token=self.generate_token(access_payload),
            refresh_token=self.generate_token(refresh_payload),
        )

    def generate_token(self, payload: JwtPayload) -> str:
        return jwt.encode(
            payload=payload.model_dump(mode="json"),
            key=self.config.secret_key,
            algorithm=self.config.hash_algorithm,
        )

    def is_valid_access_token(self, access_token: str) -> bool:
        return self.decode_payload(token=access_token) is not None

    def decode_access_token(self, access_token: str, **kwargs) -> Optional[JwtPayload]:
        return self.decode_payload(token=access_token, **kwargs)

    def decode_payload(self, token: bytes | str, **kwargs) -> Optional[JwtPayload]:
        try:
            decoded = jwt.decode(
                jwt=token,
                key=self.config.secret_key,
                algorithms=self.config.hash_algorithm,
                **kwargs,
            )
            return JwtPayload(**decoded)
        except jwt.InvalidTokenError:
            return None

    def payload_from_user(self, user: Any) -> Dict[str, Any]:
        return {
            UserField.as_outref(): getattr(user, UserField.ID),
            JwtKeys.LAST_LOGIN_TIME: getattr(user, UserField.LAST_LOGIN_TIME, None),
            JwtKeys.JTI: uuid4().hex,
        }

    @classmethod
    def get_payload(
        cls, expire: int | float, token_type: JwtType, **kwargs
    ) -> JwtPayload:
        iat = int(time.time())
        exp = iat + expire
        kwargs.update(
            {
                JwtKeys.IAT: iat,
                JwtKeys.EXP: exp,
                JwtKeys.TOKEN_TYPE: token_type,
            }
        )
        return JwtPayload(**kwargs)
