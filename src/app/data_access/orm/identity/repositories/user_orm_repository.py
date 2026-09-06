from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.application.identity.dto.forgot_dto import ForgotPasswordStep2ResponseDTO
from src.app.application.identity.dto.user_dto import (
    UserAuthDTO,
    UserCredentialsDTO,
    UserDetailedDTO,
    UserListDTO,
)
from src.app.data_access.orm.base.base_orm_models import STATUS_ACTIVE
from src.app.data_access.orm.base.base_orm_repository import SqlAlchemyRepository
from src.app.data_access.orm.blob.models.blob_orm_model import BlobObjectOrmModel
from src.app.data_access.orm.identity.filter_compilers import UserFilterCompiler
from src.app.data_access.orm.identity.models.user_orm_model import UserOrmModel
from src.app.domain.identity.aggregates.user_aggregate import UserAggregate
from src.app.domain.identity.repositories.user_repository import (
    UserAccountRepositoryProto,
    UserQueryRepositoryProto,
    UserRepositoryProto,
)
from src.app.infra.functions.url import make_media_full_url
from src.app.modules.filtering.types import FilterContainerCollection
from src.app.shared_kernel.params.ordering import OrderingContainer
from src.app.shared_kernel.ports.factories.entity_source_factory import (
    EntitySourceFactoryProto,
)
from src.app.shared_kernel.pydantic.types import ListQueryResponse
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.types.context_dtos import UserOnContextDTO
from src.app.shared_kernel.types.entities import UserBase
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)


def _full_name(first_name: Optional[str], last_name: Optional[str]) -> str:
    return f"{first_name or ''} {last_name or ''}".strip()


class UserOrmRepository(
    SqlAlchemyRepository[UserOrmModel],
    UserRepositoryProto,
    UserAccountRepositoryProto,
    UserQueryRepositoryProto,
):
    """Write side + the reads the auth flows need.

    Nothing here loads the whole ORM row when a handful of columns will do: the
    hot paths (token verification on every request, login) run once per call, so
    they select exactly what they use.
    """

    model = UserOrmModel
    filter_compiler = UserFilterCompiler(model=UserOrmModel)

    def __init__(
        self, db: AsyncSession, source_factory: EntitySourceFactoryProto
    ) -> None:
        super().__init__(db=db)
        self._source_factory = source_factory

    # ----- write ---------------------------------------------------------- #

    def create(self, obj: UserAggregate) -> None:
        self.db.add(obj.source.build_root())

    async def get_aggregate_for_update(self, id_: ID_T) -> Optional[UserAggregate]:
        found = await self._get_by_id(id_)

        if found is None:
            return None

        return UserAggregate(source=self._source_factory.from_source(found))

    async def get_aggregate_for_update_by_email(
        self, email: str
    ) -> Optional[UserAggregate]:
        found = await self._get_by_field("email", email)

        if found is None:
            return None

        return UserAggregate(source=self._source_factory.from_source(found))

    async def get_for_password_reset(self, email: str) -> Optional[UserAggregate]:
        return await self.get_aggregate_for_update_by_email(email=email)

    # ----- read ----------------------------------------------------------- #

    async def get_by_id(self, id_: ID_T) -> Optional[UserBase]:
        return await self._get_by_id(id_)

    async def get_for_context(self, id_: ID_T) -> Optional[UserOnContextDTO]:
        """The per-request identity. Returns a detached value, not an ORM row,
        so reading it after the session closes cannot raise."""
        stmt = select(
            self.model.id,
            self.model.email,
            self.model.first_name,
            self.model.last_name,
            self.model.is_active,
        ).where(self.model.id == id_)

        row = (await self.db.execute(stmt)).mappings().one_or_none()

        if row is None:
            return None

        return UserOnContextDTO(
            id=row["id"],
            email=row["email"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            is_active=row["is_active"],
        )

    async def exists_by_email(
        self, email: str, is_active: Optional[bool] = None
    ) -> bool:
        conditions = [self.model.email == email]

        if is_active is not None:
            conditions.append(self.model.is_active.is_(is_active))

        return await self._exists(*conditions)

    async def get_credentials_by_email(self, email: str) -> Optional[UserAuthDTO]:
        stmt = select(
            self.model.id,
            self.model.email,
            self.model.password,
            self.model.is_active,
            self.model.email_confirmed,
            self.model.last_login_time,
        ).where(self.model.email == email)

        row = (await self.db.execute(stmt)).mappings().one_or_none()

        if row is None:
            return None

        return UserAuthDTO(
            id=row["id"],
            email=row["email"],
            # A user who has no usable password yet stores "" — the password
            # service refuses to verify against it rather than raising.
            password=row["password"] or "",
            is_active=row["is_active"],
            email_confirmed=row["email_confirmed"],
            last_login_time=row["last_login_time"],
        )

    async def get_by_email_for_password_recovery(
        self, email: str
    ) -> Optional[ForgotPasswordStep2ResponseDTO]:
        stmt = (
            select(
                self.model.id,
                self.model.email,
                self.model.first_name,
                self.model.last_name,
                BlobObjectOrmModel.path.label("avatar_path"),
            )
            .outerjoin(BlobObjectOrmModel, BlobObjectOrmModel.id == self.model.avatar_id)
            .where(self.model.email == email)
        )

        row = (await self.db.execute(stmt)).mappings().one_or_none()

        if row is None:
            return None

        return ForgotPasswordStep2ResponseDTO(
            id=row["id"],
            full_name=_full_name(row["first_name"], row["last_name"]),
            email=row["email"],
            avatar_url=(
                make_media_full_url(row["avatar_path"]) if row["avatar_path"] else None
            ),
        )

    # ----- account -------------------------------------------------------- #

    async def exists(self, id_: ID_T) -> bool:
        return await self._exists(self.model.id == id_)

    async def toggle_status(self, id_: ID_T) -> bool:
        """Flip active/inactive in one statement.

        `status` and `is_active` are written together — they are two views of the
        same fact, and letting them drift is what makes "active but unusable"
        accounts appear.
        """
        stmt = (
            update(self.model)
            .where(self.model.id == id_)
            .values(
                status=func.abs(self.model.status - STATUS_ACTIVE),
                is_active=~self.model.is_active,
            )
        )

        result = await self.db.execute(stmt)
        return result.rowcount == 1

    async def activate(self, user_id: ID_T) -> Optional[UserCredentialsDTO]:
        stmt = (
            update(self.model)
            .where(self.model.id == user_id)
            .values(
                is_active=True, status=STATUS_ACTIVE, email_confirmed=True
            )
            .returning(
                self.model.id,
                self.model.email,
                self.model.first_name,
                self.model.last_name,
            )
        )

        row = (await self.db.execute(stmt)).mappings().one_or_none()

        if row is None:
            return None

        return UserCredentialsDTO(
            id=row["id"],
            email=row["email"],
            full_name=_full_name(row["first_name"], row["last_name"]),
        )

    async def get_credentials_for_resend(
        self, user_id: ID_T
    ) -> Optional[UserCredentialsDTO]:
        stmt = select(
            self.model.id,
            self.model.email,
            self.model.first_name,
            self.model.last_name,
        ).where(self.model.id == user_id)

        row = (await self.db.execute(stmt)).mappings().one_or_none()

        if row is None:
            return None

        return UserCredentialsDTO(
            id=row["id"],
            email=row["email"],
            full_name=_full_name(row["first_name"], row["last_name"]),
        )

    # ----- queries -------------------------------------------------------- #

    async def get_list(
        self,
        limit: int,
        offset: int,
        filters: FilterContainerCollection,
        ordering: Optional[OrderingContainer] = None,
    ) -> ListQueryResponse[UserListDTO]:
        conditions = self._compile_filters(filters)

        stmt = (
            select(
                self.model.id,
                self.model.email,
                self.model.first_name,
                self.model.last_name,
                self.model.phone,
                self.model.status,
                self.model.created_at,
                BlobObjectOrmModel.thumbnail_path.label("avatar_path"),
            )
            .outerjoin(BlobObjectOrmModel, BlobObjectOrmModel.id == self.model.avatar_id)
            .where(*conditions)
        )

        count = (
            await self.db.execute(
                select(func.count()).select_from(
                    select(self.model.id).where(*conditions).subquery()
                )
            )
        ).scalar_one()

        stmt = self._apply_ordering(stmt, ordering).limit(limit).offset(offset)
        rows = (await self.db.execute(stmt)).mappings().all()

        return ListQueryResponse(
            count=count,
            rows=[
                UserListDTO(
                    id=row["id"],
                    email=row["email"],
                    full_name=_full_name(row["first_name"], row["last_name"]),
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    phone=row["phone"],
                    status=row["status"],
                    created_at=row["created_at"],
                    avatar_url=(
                        make_media_full_url(row["avatar_path"])
                        if row["avatar_path"]
                        else None
                    ),
                )
                for row in rows
            ],
        )

    async def get_detailed(self, id_: ID_T) -> Optional[UserDetailedDTO]:
        stmt = (
            select(
                self.model,
                BlobObjectOrmModel.path.label("avatar_path"),
            )
            .outerjoin(BlobObjectOrmModel, BlobObjectOrmModel.id == self.model.avatar_id)
            .where(self.model.id == id_)
        )

        row = (await self.db.execute(stmt)).one_or_none()

        if row is None:
            return None

        user, avatar_path = row

        return UserDetailedDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            address=user.address,
            description=user.description,
            information=user.information,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at,
            email_confirmed=user.email_confirmed,
            is_active=user.is_active,
            last_login_time=user.last_login_time,
            avatar_url=make_media_full_url(avatar_path) if avatar_path else None,
        )


ensure_isimplementation(UserOrmRepository, UserRepositoryProto)
ensure_isimplementation(UserOrmRepository, UserAccountRepositoryProto)
ensure_isimplementation(UserOrmRepository, UserQueryRepositoryProto)
