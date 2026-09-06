from typing import Optional

from sqlalchemy import Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from src.app.application.blob.constants import constraints
from src.app.application.blob.constants.enums import BlobKindEnum
from src.app.data_access.orm.base.base_orm_models import (
    AuthorInfoModelMixin,
    ChronoModelMixin,
    SqlAlchemyBaseModel,
)
from src.app.data_access.orm.constants.db_constants import DatabaseTable


class BlobObjectOrmModel(
    SqlAlchemyBaseModel, ChronoModelMixin, AuthorInfoModelMixin
):
    """One stored object — a raw file or an image with its derived variants.

    Paths are stored *relative to the media root* (``images/<uuid>.webp``), never
    with a leading ``/media``: the root belongs to the deployment, not the row, so
    it can move without rewriting every record. Readers prepend it when building a
    URL.
    """

    __tablename__ = DatabaseTable.BLOB_OBJECT

    name: Mapped[str] = mapped_column(
        String(constraints.BLOB_NAME_MAX_LENGTH), nullable=False
    )

    kind: Mapped[BlobKindEnum] = mapped_column(
        SmallInteger, nullable=False, default=BlobKindEnum.RAW
    )

    content_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # The stored bytes. For an image this is the (possibly re-encoded) original.
    path: Mapped[str] = mapped_column(
        String(constraints.BLOB_PATH_MAX_LENGTH), nullable=False
    )

    # Image-only derivatives; NULL for RAW blobs.
    medium_path: Mapped[Optional[str]] = mapped_column(
        String(constraints.BLOB_PATH_MAX_LENGTH), nullable=True
    )
    thumbnail_path: Mapped[Optional[str]] = mapped_column(
        String(constraints.BLOB_PATH_MAX_LENGTH), nullable=True
    )

    @property
    def extension(self) -> str:
        return self.name.rsplit(".", 1)[-1] if "." in self.name else ""
