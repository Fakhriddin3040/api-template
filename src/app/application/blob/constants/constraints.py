BLOB_NAME_MAX_LENGTH = 255
BLOB_PATH_MAX_LENGTH = 500

MAX_BLOB_SIZE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

DEFAULT_FILE_EXTENSION = "bin"

# Longest edge of each generated image variant, in pixels.
IMAGE_MEDIUM_MAX_EDGE = 1024
IMAGE_THUMBNAIL_MAX_EDGE = 256

# Magic bytes a payload must start with for its claimed extension. An empty
# tuple means "no signature to check" (plain text).
ALLOWED_FILE_SIGNATURES = {
    "pdf": (b"%PDF-",),
    "zip": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
    "rar": (b"Rar!\x1a\x07\x00", b"Rar!\x1a\x07\x01\x00"),
    "docx": (b"PK\x03\x04",),
    "xlsx": (b"PK\x03\x04",),
    "pptx": (b"PK\x03\x04",),
    "csv": (),
    "txt": (),
}

ALLOWED_IMAGE_SIGNATURES = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "gif": (b"GIF87a", b"GIF89a"),
    "webp": (b"RIFF",),
}
