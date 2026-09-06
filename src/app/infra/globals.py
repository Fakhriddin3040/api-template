from typing import ClassVar

from src.app.infra.di.root_di import RootDIContainer


class DIContainerRegistry:
    #! Readonly
    __root: ClassVar[RootDIContainer | None] = None

    @classmethod
    def set_root_container(cls, root: RootDIContainer) -> None:
        if cls.__root is None:
            cls.__root = root
            return

        raise ValueError("Root di container is read only!")

    @classmethod
    def get_root_container(cls) -> RootDIContainer:
        return cls.__root
