"""Local-filesystem blob storage with a minimal image pipeline.

Everything above ``BlobStorageProto`` is storage-agnostic; this adapter is the
only place that knows about directories and Pillow. An S3/MinIO adapter is a
second implementation of the same protocol.

TODO: finish after migration — object-storage backend (S3/MinIO), content-type
sniffing and EXIF stripping are out of scope for the template.
"""

import asyncio
import logging
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

from src.app.application.blob.constants.constraints import (
    IMAGE_MEDIUM_MAX_EDGE,
    IMAGE_THUMBNAIL_MAX_EDGE,
)
from src.app.application.blob.constants.enums import BlobKindEnum
from src.app.application.blob.dto.blob_dto import StoredBlobDTO
from src.app.application.blob.ports.storage import BlobStorageProto
from src.app.shared_kernel.config.app_config import AppConfig
from src.app.shared_kernel.utils.functions.uuid_funcs import uuid7
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)

logger = logging.getLogger(__name__)

_VARIANTS: Tuple[Tuple[str, int], ...] = (
    ("medium", IMAGE_MEDIUM_MAX_EDGE),
    ("thumbnail", IMAGE_THUMBNAIL_MAX_EDGE),
)


class LocalBlobStorage(BlobStorageProto):
    def __init__(self, app_config: AppConfig) -> None:
        self._config = app_config

    async def store(
        self, *, content: memoryview, name: str, kind: BlobKindEnum
    ) -> StoredBlobDTO:
        # Pillow work and disk writes are blocking; keep them off the loop.
        return await asyncio.to_thread(self._store_sync, content, name, kind)

    async def delete(self, paths: List[str]) -> None:
        await asyncio.to_thread(self._delete_sync, paths)

    # ----- sync internals ------------------------------------------------- #

    def _store_sync(
        self, content: memoryview, name: str, kind: BlobKindEnum
    ) -> StoredBlobDTO:
        extension = name.rsplit(".", 1)[-1].lower() if "." in name else "bin"
        stem = str(uuid7())
        relative_dir = (
            self._config.image_path
            if kind == BlobKindEnum.IMAGE
            else self._config.file_path
        )

        original = self._write(relative_dir, f"{stem}.{extension}", content)

        if kind != BlobKindEnum.IMAGE:
            return StoredBlobDTO(path=original)

        variants = self._make_image_variants(content, relative_dir, stem)

        return StoredBlobDTO(
            path=original,
            medium_path=variants.get("medium"),
            thumbnail_path=variants.get("thumbnail"),
        )

    def _make_image_variants(
        self, content: memoryview, relative_dir: Path, stem: str
    ) -> dict[str, Optional[str]]:
        """Down-scaled copies of an image, longest edge capped per variant.

        A failure here is not fatal: the original is already stored, so the blob
        stays usable and simply has no derivatives.
        """
        try:
            from PIL import Image
        except ImportError:  # pragma: no cover - Pillow is a declared dependency
            logger.warning("Pillow is unavailable; storing image without variants")
            return {}

        out: dict[str, Optional[str]] = {}

        for variant, max_edge in _VARIANTS:
            try:
                with Image.open(BytesIO(bytes(content))) as image:
                    image = image.convert("RGB")
                    image.thumbnail((max_edge, max_edge))

                    buffer = BytesIO()
                    image.save(buffer, format="WEBP", quality=82)

                out[variant] = self._write(
                    relative_dir / variant,
                    f"{stem}.webp",
                    memoryview(buffer.getvalue()),
                )
            except Exception:  # noqa: BLE001 - variants are best-effort
                logger.exception("Failed to build the %r image variant", variant)
                out[variant] = None

        return out

    def _write(self, relative_dir: Path, filename: str, content: memoryview) -> str:
        """Write under the configured root and return the *relative* path.

        The relative value is what gets persisted: the media root belongs to the
        deployment, not to the row, so it can move without a data migration.
        """
        absolute_dir = self._config.media_root / relative_dir
        absolute_dir.mkdir(parents=True, exist_ok=True)
        (absolute_dir / filename).write_bytes(content)

        return (relative_dir / filename).as_posix()

    def _delete_sync(self, paths: List[str]) -> None:
        for path in paths:
            if not path:
                continue
            absolute = self._config.media_root / self._strip_root(path)
            Path(absolute).unlink(missing_ok=True)

    @staticmethod
    def _strip_root(path: str) -> Path:
        """Normalise a stored path to media-relative.

        Tolerates a leading ``/media/`` so a value written by an older convention
        still resolves to the right file.
        """
        return Path(path.removeprefix("/").removeprefix("media/"))


ensure_isimplementation(LocalBlobStorage, BlobStorageProto)
