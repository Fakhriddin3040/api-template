"""Local development entrypoint: `python serve.py`.

Production runs the same app object through the uvicorn CLI (see
`scripts/start_api.sh`); this file exists so a fresh clone starts with one
command and no arguments to remember.
"""

import uvicorn

from src.config.asgi import app  # noqa: F401  (imported for `serve:app`)

if __name__ == "__main__":
    uvicorn.run(
        app="serve:app",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True,
    )
