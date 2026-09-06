from typing import Protocol, runtime_checkable


@runtime_checkable
class SecretServiceProto(Protocol):
    def generate(self, length: int, /) -> bytes:
        """Generates 64-bit random bytes"""

    def generate_b64(self, length: int, /) -> bytes:
        """Generates 64-bit random bytes and returns base64 decoded string"""
