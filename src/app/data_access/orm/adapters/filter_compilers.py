import inspect
from typing import Callable, Dict, Mapping, Optional, Set, Type, Tuple, Any

from sqlalchemy import ColumnExpressionArgument

from src.app.data_access.orm.base.base_orm_models import SqlAlchemyBaseModel
from src.app.modules.filtering.enums import FilterLookupEnum
from src.app.modules.filtering.ports import FilterCompilerProto
from src.app.modules.filtering.types import (
    FilterContainerCollection,
    FilterContainer,
)
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)

# Reserved `meta` key carrying the read model's scope. Consumed by `_compile`
# for method lookup and stripped before `meta` reaches a `compile_*` override,
# so overrides never see it among their per-request context.
SCOPE_META_KEY = "scope"

# Per-function cache of "does this `compile_*` method accept a `**meta` bag?".
# Keyed by the underlying function object so bound-method identity is irrelevant.
_META_AWARE_CACHE: Dict[Callable[..., Any], bool] = {}


def _accepts_meta(method: Callable[..., Any]) -> bool:
    """True if `method` declares `**kwargs`, i.e. it opts in to the meta bag.

    Methods without a VAR_KEYWORD parameter (every legacy `compile_*` override)
    are treated as meta-unaware and called as `method(container)`.
    """
    func = getattr(method, "__func__", method)
    cached = _META_AWARE_CACHE.get(func)
    if cached is None:
        cached = any(
            p.kind is inspect.Parameter.VAR_KEYWORD
            for p in inspect.signature(func).parameters.values()
        )
        _META_AWARE_CACHE[func] = cached
    return cached


def compile_range(
    column: Any, value: Tuple[Any, Any], field: str = "?"
) -> ColumnExpressionArgument[Any]:
    """RANGE lookup against any column-like expression, including one-sided
    ranges (`"100,"` / `",100"`).

    Always use this instead of a bare `column.between(low, high)`: `between`
    with a `None` endpoint compiles to `BETWEEN NULL AND ...`, which matches no
    rows instead of raising.
    """
    low, high = value

    if low is not None and high is not None:
        return column.between(low, high)
    if low is not None:
        return column >= low
    if high is not None:
        return column <= high

    raise RuntimeError(
        f"Range filter `{field}` has no boundary; "
        f"FilterValidator should have rejected it."
    )


class SqlAlchemyFiltersCompiler[TModel: SqlAlchemyBaseModel]:
    """
    Notes:
        Any checks for column existence or developer-depended errors
            must not have a check inside on this type
        State must not be changed in any time

        `compile()` accepts an optional `**meta` bag of per-request context
        (a subquery, a statement, loader options, ...). It is forwarded to a
        `compile_<field>__<lookup>` override **only when that method declares
        `**kwargs`**; a meta-aware override therefore looks like
        `def compile_x__eq(self, container, *, agg, **meta): ...` and picks what
        it needs.

    Scopes:
        One compiler per model. When two read models expose the *same* field
        with different semantics, the caller passes `scope=` and the compiler
        looks for a scoped method first::

            compile_<scope>__<field>__<lookup>   # scoped
            compile_<field>__<lookup>            # shared / default

        So `subject_id` can mean the debit side on one route and the credit side
        on another without a second compiler and without the query DTO knowing
        anything::

            class DocFiltersCompiler(SqlAlchemyFiltersCompiler):
                scopes = {"sales", "purchases"}
                scoped_fields = {"subject_id"}

                def compile_sales__subject_id__eq(self, c): ...
                def compile_purchases__subject_id__eq(self, c): ...

            repo.filter_compiler.compile(filters, scope="sales")

        `scopes` and `scoped_fields` make the dispatch checked rather than
        stringly-typed. An unknown `scope`, or a `scoped_fields` entry reached
        with no scope / with no matching scoped method, raises: a field declared
        scope-dependent can never silently fall back to another scope's
        behaviour, which is the whole point of naming them.

        Resolution order is: scoped method -> unscoped method (only if `field`
        is not in `scoped_fields`) -> the generic column path.
    """

    # Optional allow-list of scope names. Empty = this compiler is unscoped and
    # passing `scope=` to it is an error.
    scopes: Set[str] = frozenset()

    # Fields whose meaning is scope-dependent. Reaching one without resolving a
    # scoped method is a bug, so it raises instead of using the generic column.
    scoped_fields: Set[str] = frozenset()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Rejects a half-declared scope matrix at import time.

        Every `scoped_fields` entry must have a `compile_<scope>__<field>__
        <lookup>` for *every* declared scope, otherwise the omission would only
        surface on the first request that happens to use that filter.
        """
        super().__init_subclass__(**kwargs)

        if not cls.scoped_fields:
            return

        if not cls.scopes:
            raise TypeError(
                f"{cls.__name__} declares scoped_fields="
                f"{sorted(cls.scoped_fields)} but no `scopes`."
            )

        declared = {
            name.removeprefix("compile_")
            for name in dir(cls)
            if name.startswith("compile_")
        }
        missing = [
            f"compile_{scope}__{field}__<lookup>"
            for field in sorted(cls.scoped_fields)
            for scope in sorted(cls.scopes)
            # The lookup is whatever the query DTO declares for that field, so
            # accept any: only the (scope, field) pair is knowable statically.
            if not any(name.startswith(f"{scope}__{field}__") for name in declared)
        ]

        if missing:
            raise TypeError(
                f"{cls.__name__} declares scoped fields without a handler for "
                f"every scope. Missing: {', '.join(missing)}"
            )

    def __init__(self, model: Type[TModel]) -> None:
        self.model = model

    def compile(
        self, containers: FilterContainerCollection, /, **meta: Any
    ) -> Tuple[ColumnExpressionArgument[Any], ...]:
        """Compiles filter field containers into SQLAlchemy where-expressions.

        `scope` selects between same-named filters that differ per read model;
        it is consumed here and never forwarded to the overrides.
        """
        scope = meta.pop(SCOPE_META_KEY, None)

        if scope is not None and scope not in self.scopes:
            raise RuntimeError(
                f"{type(self).__name__} got unknown scope `{scope}`; "
                f"declared scopes: {sorted(self.scopes) or '(none)'}."
            )

        return tuple(
            self._compile(spec, meta, scope)
            for spec in containers
            if not self._is_absent(spec)
        )

    @staticmethod
    def _is_absent(container: FilterContainer) -> bool:
        """Whether a container carries no constraint and should be skipped.

        An empty JSON/IN payload means "no constraint", not "match nothing" --
        `FilterValidator` already treats it as absent for the `required` check,
        and compiling it would silently exclude every row (`col IN ()`, or an
        array-contains against a NULL column).
        """
        if container.value is None:
            return True

        return (
            container.lookup
            in (
                FilterLookupEnum.JSON,
                FilterLookupEnum.IN,
            )
            and not container.value
        )

    def _resolve(
        self, container: FilterContainer, scope: Optional[str]
    ) -> Optional[Callable[..., ColumnExpressionArgument[Any]]]:
        """Finds the override for a container: the scoped one if a scope is
        active, else the shared one."""
        suffix = f"{container.field}__{container.lookup}"

        if scope is not None:
            scoped = getattr(self, f"compile_{scope}__{suffix}", None)

            if scoped is not None:
                return scoped

        if container.field in self.scoped_fields:
            if scope is None:
                raise RuntimeError(
                    f"{type(self).__name__} declares `{container.field}` as "
                    f"scope-dependent, so the caller must pass `scope=` "
                    f"(one of {sorted(self.scopes)}) to compile it."
                )

            raise RuntimeError(
                f"{type(self).__name__} declares `{container.field}` as "
                f"scope-dependent but `compile_{scope}__{suffix}` does not "
                f"exist. Add that method, or drop the field from "
                f"`scoped_fields` if it no longer varies by read model."
            )

        return getattr(self, f"compile_{suffix}", None)

    def _compile(
        self,
        container: FilterContainer,
        meta: Optional[Mapping[str, Any]] = None,
        scope: Optional[str] = None,
    ) -> ColumnExpressionArgument[Any]:
        method = self._resolve(container, scope)

        if method is not None:
            if meta and _accepts_meta(method):
                return method(container, **meta)
            return method(container)

        if container.lookup == FilterLookupEnum.JSON:
            raise RuntimeError(
                f"{type(self).__name__} has no handler for JSON filter "
                f"`{container.field}`. A structured payload has no generic "
                f"column mapping, so it needs an explicit "
                f"`compile_{container.field}__{FilterLookupEnum.JSON}` method."
            )

        column = getattr(self.model, container.field, None)

        if column is None:
            raise RuntimeError(
                f"{type(self).__name__} cannot compile filter `{container.field}"
                f"__{container.lookup}`: {self.model.__name__} has no such column "
                f"and no `compile_{container.field}__{container.lookup}` override "
                f"is declared."
            )

        if container.lookup == FilterLookupEnum.EQ:
            return column == container.value

        if container.lookup == FilterLookupEnum.RANGE:
            return compile_range(column, container.value, container.field)

        if container.lookup == FilterLookupEnum.IN:
            return column.in_(container.value)

        if container.lookup == FilterLookupEnum.GT:
            return column > container.value

        if container.lookup == FilterLookupEnum.LT:
            return column < container.value

        if container.lookup == FilterLookupEnum.GTE:
            return column >= container.value

        if container.lookup == FilterLookupEnum.LTE:
            return column <= container.value

        raise RuntimeError(f"Unknown filter lookup {container.lookup}.")

    def compile_search__eq(
        self, container: FilterContainer
    ) -> ColumnExpressionArgument[Any]:
        # Raises an error if model has not name
        # so, if you have a specific search compilation,
        # create filter compiler for model and handle re-define
        # this method
        return self.model.name.ilike(f"{container.value}%")


ensure_isimplementation(SqlAlchemyFiltersCompiler, FilterCompilerProto[Any])
