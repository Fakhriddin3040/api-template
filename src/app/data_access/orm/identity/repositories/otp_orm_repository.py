from typing import Optional

from sqlalchemy import and_, func, select, true, update

from src.app.application.identity.dto.user_dto import OtpCreateDTO, OTPDetailedDTO
from src.app.data_access.orm.base.base_orm_repository import SqlAlchemyRepository
from src.app.data_access.orm.identity.models.user_orm_model import OtpOrmModel
from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.domain.identity.repositories.otp_repository import OtpRepositoryProto
from src.app.shared_kernel.constants.common_enums import ContentTypeEnum
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)

_DETAIL_COLUMNS = (
    OtpOrmModel.id,
    OtpOrmModel.otp,
    OtpOrmModel.content_id,
    OtpOrmModel.expires_at,
    OtpOrmModel.target_value,
    OtpOrmModel.verified,
    OtpOrmModel.used_at,
)


def _to_detailed(row) -> Optional[OTPDetailedDTO]:
    if row is None:
        return None

    return OTPDetailedDTO(
        id=row["id"],
        otp=row["otp"],
        content_id=row["content_id"],
        expires_at=row["expires_at"],
        target_value=row["target_value"],
        verified=row["verified"],
        used_at=row["used_at"],
    )


class OtpOrmRepository(SqlAlchemyRepository[OtpOrmModel], OtpRepositoryProto):
    model = OtpOrmModel

    def create(self, data: OtpCreateDTO) -> None:
        obj = self.model(
            otp=data.otp,
            content_id=data.content_id,
            content_type=data.content_type,
            kind=data.kind,
            expires_at=data.expires_at,
            target_value=data.target_value,
            verified=data.verified,
        )

        self.db.add(obj)

    async def find_active_by_otp(
        self,
        otp: str,
        kind: OtpKindEnum,
        content_type: ContentTypeEnum,
    ) -> Optional[OTPDetailedDTO]:
        """Look up an OTP by its secret alone.

        Only safe for high-entropy secrets. The numeric codes this template
        mails are *not* unique, so those flows must use
        ``find_active_for_content`` instead.
        """
        stmt = select(*_DETAIL_COLUMNS).where(
            self.model.otp == otp,
            self.model.kind == kind,
            self.model.content_type == content_type,
        )

        return _to_detailed((await self.db.execute(stmt)).mappings().one_or_none())

    async def find_active_for_content(
        self,
        otp: str,
        content_id: ID_T,
        kind: OtpKindEnum,
        content_type: ContentTypeEnum,
    ) -> Optional[OTPDetailedDTO]:
        stmt = (
            select(*_DETAIL_COLUMNS)
            .where(
                self.model.otp == otp,
                self.model.content_id == content_id,
                self.model.kind == kind,
                self.model.content_type == content_type,
            )
            # Codes are reissued, and an old row can share a value with the
            # current one; newest wins.
            .order_by(self.model.created_at.desc())
            .limit(1)
        )

        return _to_detailed((await self.db.execute(stmt)).mappings().one_or_none())

    async def consume_by_id(self, id_: ID_T, now_epoch: int) -> bool:
        """Atomically claim an unused OTP. True only for the caller that won."""
        stmt = (
            update(self.model)
            .where(
                self.model.id == id_,
                # The guard is what makes this atomic: two concurrent requests
                # both match the row, but only the first one's WHERE still holds.
                self.model.used_at.is_(None),
                self.model.expires_at >= now_epoch,
            )
            .values(used_at=now_epoch, verified=true())
        )

        result = await self.db.execute(stmt)
        return result.rowcount == 1

    async def has_recent_issue(
        self,
        content_id: ID_T,
        content_type: ContentTypeEnum,
        kind: OtpKindEnum,
        cooldown_minutes: int,
    ) -> bool:
        stmt = select(
            select(self.model.id)
            .where(
                self.model.content_id == content_id,
                self.model.content_type == content_type,
                self.model.kind == kind,
                self.model.created_at
                >= func.now() - func.make_interval(0, 0, 0, 0, 0, cooldown_minutes),
            )
            .exists()
        )

        return bool((await self.db.execute(stmt)).scalar())

    async def invalidate_pending(
        self,
        content_id: ID_T,
        content_type: ContentTypeEnum,
        kind: OtpKindEnum,
        now_epoch: int,
    ) -> None:
        """Burn every still-usable code for this (owner, kind).

        Issuing a new code must retire the old one, or a leaked earlier code
        would stay valid for its full TTL alongside the replacement.
        """
        stmt = (
            update(self.model)
            .where(
                and_(
                    self.model.content_id == content_id,
                    self.model.content_type == content_type,
                    self.model.kind == kind,
                    self.model.used_at.is_(None),
                )
            )
            .values(used_at=now_epoch)
        )

        await self.db.execute(stmt)


ensure_isimplementation(OtpOrmRepository, OtpRepositoryProto)
