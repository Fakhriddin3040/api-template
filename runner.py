"""Telemetry daemon entrypoint: `python runner.py`.

A thin shim so the daemon starts the same way the API does (a file at the repo
root). The implementation lives in the telemetry module.
"""

from src.app.modules.telemetry.runner import main

if __name__ == "__main__":
    main()
