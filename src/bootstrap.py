"""Application bootstrapping.

Two entry points, both idempotent:

* ``init_di_containers`` builds and wires the DI graph. It runs at import time so
  ``@inject`` decorators resolve before any route or event handler is built.
* ``bootstrap_async`` is the lifespan hook for anything that needs a running
  event loop.
"""

import asyncio
import logging
import threading
from types import ModuleType
from typing import Callable, Iterable, Literal, Optional

import src.app
from src.app.infra.di.root_di import RootDIContainer
from src.app.infra.globals import DIContainerRegistry
from src.app.shared_kernel.utils.di_funcs import wire_recursive

logger = logging.getLogger("bootstrap")


class Bootstrap:
    _async_lock: asyncio.Lock | None = None
    _sync_lock = threading.RLock()
    _project_init_done = False
    _project_stage: Literal["STARTUP", "LISTENING", "SHUTDOWN"] | None = None
    _ready_event: asyncio.Event | None = None
    _di_init_done: bool = False

    @classmethod
    async def bootstrap_async(cls) -> None:
        logger.debug("Async bootstrapping application.")

        if cls._project_init_done:
            return

        if cls._async_lock is None:
            with cls._sync_lock:
                if cls._ready_event is None:
                    cls._ready_event = asyncio.Event()
                if cls._async_lock is None:
                    cls._async_lock = asyncio.Lock()

        async with cls._async_lock:
            if cls._project_init_done:
                return

            if not cls._di_init_done:
                cls.init_di_containers()

            cls._project_init_done = True

            if cls._ready_event is not None:
                cls._ready_event.set()

            logger.info("Application bootstrapping finished.")

    @classmethod
    async def wait_ready(cls) -> None:
        if cls._project_init_done:
            return

        if cls._ready_event is None:
            with cls._sync_lock:
                if cls._ready_event is None:
                    cls._ready_event = asyncio.Event()

        await cls._ready_event.wait()

    @classmethod
    def init_di_containers(cls) -> Optional[RootDIContainer]:
        with cls._sync_lock:
            if cls._di_init_done:
                return None

            def _after_wire(modules: Iterable[ModuleType]) -> None:
                # A module exposing `setup()` registers itself (CQRS handlers,
                # event subscriptions) once its own injections are resolvable.
                for mod in modules:
                    setup = getattr(mod, "setup", None)

                    if isinstance(setup, Callable):
                        setup()

            logger.info("Initializing DI containers...")

            root = RootDIContainer()
            DIContainerRegistry.set_root_container(root)

            wire_recursive(container=root, package=src.app, after_wire=_after_wire)

            cls._di_init_done = True
            logger.info("DI containers initialized successfully.")
            return root
