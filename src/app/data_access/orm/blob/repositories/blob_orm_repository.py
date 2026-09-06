from typing import List, Optional

from sqlalchemy import delete, func, select

from src.app.application.blob.dto.blob_dto import (
    BlobCreateDTO,
    BlobDetailedDTO,
    BlobListDTO,
)
from src.app.application.blob.ports.blob_repository import BlobRepositoryProto
from src.app.data_access.orm.base.base_orm_repository import SqlAlchemyRepository
from src.app.data_access.orm.blob.models.blob_orm_model import BlobObjectOrmModel
from src.app.infra.functions.url import make_media_full_url
from src.app.shared_kernel.pydantic.types import ListQueryResponse
from src.app.shared_kernel.types.base_types import ID_T


class BlobOrmRepository(SqlAlchemyRepository[BlobObjectOrmModel], BlobRepositoryProto):
    model = BlobObjectOrmModel

    async def create(self, dto: BlobCreateDTO) -> BlobListDTO:
        obj = self.model(
            name=dto.name,
            kind=dto.kind,
            content_type=dto.content_type,
            size=dto.size,
            path=dto.path,
            medium_path=dto.medium_path,
            thumbnail_path=dto.thumbnail_path,
        )
        self.db.add(obj)
        await self.db.flush()

        return BlobListDTO(
            id=obj.id,
            name=obj.name,
            kind=int(obj.kind),
            url=make_media_full_url(obj.path),
        )

    async def delete(self, id_: ID_T) -> None:
        await self.db.execute(delete(self.model).where(self.model.id == id_))

    async def exist_many(self, ids: List[ID_T]) -> bool:
        if not ids:
            return True

        stmt = select(func.count(self.model.id)).where(self.model.id.in_(ids))
        found = (await self.db.execute(stmt)).scalar_one()

        # `ids` may repeat; compare against the distinct set or a duplicate would
        # read as a missing row.
        return found == len(set(ids))

    async def exist_by_id(self, id_: ID_T) -> bool:
        return await self._exists(self.model.id == id_)

    async def get_paths(self, id_: ID_T) -> List[str]:
        stmt = select(
            self.model.path, self.model.medium_path, self.model.thumbnail_path
        ).where(self.model.id == id_)
        row = (await self.db.execute(stmt)).one_or_none()

        if row is None:
            return []

        return [p for p in row if p]

    async def get_detailed(self, id_: ID_T) -> Optional[BlobDetailedDTO]:
        obj = await self._get_by_id(id_)

        if obj is None:
            return None

        return BlobDetailedDTO(
            id=obj.id,
            name=obj.name,
            kind=int(obj.kind),
            url=make_media_full_url(obj.path),
            size=obj.size,
            content_type=obj.content_type,
            extension=obj.extension,
            medium_url=(
                make_media_full_url(obj.medium_path) if obj.medium_path else None
            ),
            thumbnail_url=(
                make_media_full_url(obj.thumbnail_path) if obj.thumbnail_path else None
            ),
        )

    async def get_list(
        self, limit: int, offset: int
    ) -> ListQueryResponse[BlobListDTO]:
        stmt = (
            select(self.model)
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        count = (
            await self.db.execute(select(func.count(self.model.id)))
        ).scalar_one()

        return ListQueryResponse(
            count=count,
            rows=[
                BlobListDTO(
                    id=row.id,
                    name=row.name,
                    kind=int(row.kind),
                    url=make_media_full_url(row.path),
                )
                for row in rows
            ],
        )
