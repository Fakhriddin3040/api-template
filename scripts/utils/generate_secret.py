"""Generate the secrets a fresh clone needs in its `.env`.

    python scripts/utils/generate_secret.py
"""

import base64
import os
import secrets
import string

_ALPHABET = string.ascii_letters + string.digits


def _key(length: int = 50) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def main() -> None:
    print("APP_SECRET_KEY=" + _key())
    # 32 raw bytes, base64-encoded: AppConfig decodes it back to bytes for AES-GCM.
    print("APP_AES_KEY=" + base64.b64encode(os.urandom(32)).decode())
    # Deliberately independent of APP_SECRET_KEY — see JwtConfig.
    print("JWT_SECRET_KEY=" + _key())


if __name__ == "__main__":
    main()
