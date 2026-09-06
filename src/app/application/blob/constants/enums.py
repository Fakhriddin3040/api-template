from enum import IntEnum


class BlobKindEnum(IntEnum):
    """What a stored object is.

    Persisted in ``blob_object.kind`` — append-only.
    """

    RAW = 0
    IMAGE = 1
