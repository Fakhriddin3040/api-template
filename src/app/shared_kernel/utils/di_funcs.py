import importlib
import logging
import pkgutil
from types import ModuleType
from typing import Optional, Callable, Sequence, Set, Iterable, Any

from dependency_injector import containers, providers

logger = logging.getLogger(__name__)


def wire_recursive(
    container: containers.Container,
    package: ModuleType,
    *,
    exclude: Optional[Callable[[str], bool]] = None,
    on_error: Optional[Callable[[str, BaseException], None]] = None,
    after_wire: Optional[Callable[[Iterable[ModuleType]], None]] = None,
) -> Sequence[ModuleType]:
    """
    Рекурсивно импортирует все подмодули пакета и вызывает container.wire(modules=[...]).
    Возвращает фактически провайренные модули.

    ВНИМАНИЕ: импорт модулей выполняет их top-level код.
    Используйте exclude, чтобы отфильтровать тяжёлые/опасные модули.
    """
    if not hasattr(package, "__path__"):
        # Это не пакет — просто провайрим сам модуль
        container.wire(modules=[package])
        return (package,)

    collected: list[ModuleType] = []
    seen: Set[str] = set()

    def _walk(pkg: ModuleType) -> None:
        pkg_path = getattr(pkg, "__path__", None)
        if not pkg_path:
            return

        prefix = pkg.__name__ + "."
        for _, name, is_pkg in pkgutil.walk_packages(pkg_path, prefix):
            if exclude and exclude(name):
                continue
            if name in seen:
                continue
            seen.add(name)

            try:
                mod = importlib.import_module(name)
            except BaseException as exc:
                if on_error:
                    on_error(name, exc)
                else:
                    logger.critical("Failed to import %s: %s", name, exc)
                continue

            collected.append(mod)

            # По желанию: углубляться только по пакетам
            if is_pkg:
                _walk(mod)

    _walk(package)

    # Включаем исходный пакет тоже (часто там есть функции/роутеры)
    collected.insert(0, package)

    container.wire(modules=collected)

    if after_wire:
        after_wire(collected)

    return tuple(collected)


def call_if_provider(dep: providers.Provider | Any):
    if isinstance(dep, providers.Provider):
        return dep()
    return dep
