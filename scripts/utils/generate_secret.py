"""Generate the two secrets a fresh clone needs in its `.env`.

    python scripts/utils/generate_secret.py
"""

import base64
import os
import secrets
import string

_ALPHABET = string.ascii_letters + string.digits


def main() -> None:
    print("APP_SECRET_KEY=" + "".join(secrets.choice(_ALPHABET) for _ in range(50)))
    # 32 raw bytes, base64-encoded: AppConfig decodes it back to bytes for AES-GCM.
    print("AES_SECRET_KEY=" + base64.b64encode(os.urandom(32)).decode())


if __name__ == "__main__":
    main()
