from typing import Optional

from src.app.application.identity.dto.api_key_dto import ApiKeyCreateDTO, ApiKeyListDTO
from sqlalchemy import select
from sqlalchemy.orm import load_only, joinedload

from src.app.application.identity.ports.repositories.api_key_repository import (
    ApiKeyRepositoryProto,
)
from src.app.data_access.orm.base.base_orm_repository import SqlAlchemyRepository
from src.app.data_access.orm.identity.models.api_key_orm_model import ApiKeyOrmModel
from src.app.data_access.orm.identity.models.user_orm_model import UserOrmModel
from src.app.domain.identity.constants.enums import ApiKeyStatusEnum
from src.app.infra.inheritance.mixins import ExecutionContextMixin
from src.app.shared_kernel.types.entities import ApiKeyBase
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)


class ApiKeyOrmRepository(
    ApiKeyRepositoryProto, SqlAlchemyRepository, ExecutionContextMixin
):
    model = ApiKeyOrmModel

    async def create(self, data: ApiKeyCreateDTO) -> ApiKeyListDTO:
        obj = ApiKeyOrmModel(
            key=data.key,
            status=ApiKeyStatusEnum.ACTIVE,
            owner_id=data.owner_id,
        )
        self.db.add(obj)
        await self.db.flush()

        return ApiKeyListDTO(id=obj.id, key=obj.key)

    async def get_with_owner(self, api_key: bytes) -> Optional[ApiKeyBase]:
        """Retrieve api key detailed object with its owner

        Args:
            api_key (bytes): Crypto-signed api key

        Returns:
            ApiKeyBase: Api key detailed object
        """
        stmt = (
            select(self.model)
            .options(
                load_only(
                    self.model.id,
                    self.model.status,
                    self.model.created_at,
                    self.model.updated_at,
                    self.model.last_used_at,
                ),
                joinedload(self.model.owner).options(
                    load_only(
                        UserOrmModel.id,
                        UserOrmModel.email,
                        UserOrmModel.first_name,
                        UserOrmModel.last_name,
                        UserOrmModel.is_active,
                    )
                ),
            )
            .where(self.model.key == api_key)
        )
        return await self.db.scalar(stmt)


ensure_isimplementation(ApiKeyOrmRepository, ApiKeyRepositoryProto)
