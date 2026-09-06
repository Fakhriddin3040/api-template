import inspect
import logging
import types
from typing import (
    Literal,
    Type,
    get_origin,
    get_args,
    Union,
    TypeVar,
    Awaitable,
    Any,
    Iterable,
    List,
    Tuple,
)

from src.app.shared_kernel.utils.static_analys.static_analys_exceptions import (
    TypeAssertionException,
)

logger = logging.getLogger("static_analys.assertion")


def _is_same_type(a, b):
    return repr(a) == repr(b)


def _is_union_origin(origin) -> bool:
    """True for both union spellings.

    ``Optional[X]`` / ``Union[X, None]`` have origin ``typing.Union`` while the
    PEP 604 form ``X | None`` has origin ``types.UnionType`` — distinct objects
    that are semantically identical. Treat them the same so mixed spellings
    across a Proto and its implementation aren't flagged as mismatches.
    """
    return origin is Union or origin is types.UnionType


def ensure_isimplementation(
    target: Type | Tuple[Type, ...] | List[Type],
    *bases,
    on_err: Literal["raise", "warning"] = "raise",
) -> None:
    """Assert (at build time) that ``target`` structurally implements ``bases``.

    ``target`` may be a single class or a tuple/list of classes — each is checked
    against every base independently.
    """
    if isinstance(target, (tuple, list)):
        for one in target:
            ensure_isimplementation(one, *bases, on_err=on_err)
        return

    _is = True

    bases = bases if isinstance(bases, Iterable) else [bases]

    for base in bases:
        for name, base_attr in base.__dict__.items():
            if name.startswith("_") and name != "__call__":
                continue

            if not callable(base_attr):
                continue

            if not hasattr(target, name):
                logger.critical(f"{target.__name__} missing the attribute '{name}'")
                _is = False
                break

            target_attr = getattr(target, name)

            base_sig = inspect.signature(base_attr)
            target_sig = inspect.signature(target_attr)

            if len(base_sig.parameters) > len(target_sig.parameters):
                logger.critical(
                    f"{target.__name__}.{name} has fewer parameters than {base.__name__}.{name}"
                )
                _is = False

            for b, t in zip(
                base_sig.parameters.values(),
                target_sig.parameters.values(),
                strict=False,
            ):
                if b.name != t.name:
                    logger.critical(
                        f"param name mismatch in {name}: {b.name} != {t.name}"
                    )
                    _is = False

                if b.kind != t.kind:
                    logger.critical(f"kind mismatch in {name}: {b.kind} != {t.kind}")
                    _is = False

                if b.default is inspect._empty and t.default is not inspect._empty:
                    logger.critical(f"param {b.name} should be required")
                    _is = False

            if (
                base_sig.return_annotation is not inspect._empty
                and target_sig.return_annotation is inspect._empty
            ):
                logger.critical(f"{target.__name__}.{name} should declare return type")
                _is = False

            if not _is_return_compatible(
                base_sig.return_annotation, target_sig.return_annotation
            ):
                logger.critical(
                    f"Return type mismatch in {target.__name__}.{name}. Expected '{base_sig.return_annotation}', got '{target_sig.return_annotation}'"
                )
                _is = False

        if not _is:
            if on_err == "raise":
                raise TypeAssertionException(target, base)

            elif on_err == "warning":
                logging.warning(
                    f"{target.__name__} is not a implementation of {base.__name__} class."
                )


def _is_return_compatible(base_ann, target_ann) -> bool:
    # Base does not specify a return annotation → ok
    if base_ann is inspect._empty:
        return True

    # Target must specify type if base does
    if target_ann is inspect._empty:
        return False

    # Handle "Any"
    if base_ann is Any:
        return True

    # An implementation that restates the base's annotation verbatim is
    # compatible by definition. Worth short-circuiting because the structural
    # rules below cannot express it for a multi-member union: they compare one
    # option at a time, and no single option equals the whole union.
    if base_ann == target_ann:
        return True

    # A base TypeVar binds to anything (incl. Optional[...]), so it matches any
    # target. Must run before the optional-rejection guards below, otherwise a
    # concrete Optional target would be wrongly rejected against a generic base
    # (e.g. CQHandler.__call__ -> Union[R, Awaitable[R]] vs Optional[DTO]).
    if isinstance(base_ann, TypeVar):
        return True

    # Extract origins
    base_origin = get_origin(base_ann)
    target_origin = get_origin(target_ann)
    base_args = get_args(base_ann)
    target_args = get_args(target_ann)

    # OPTIONAL / NONE HANDLING
    # base: Optional[T] (Union[T, NoneType])
    # target: Optional[T]
    if _is_union_origin(base_origin) and type(None) in base_args:
        # Every non-None option, not just the first: a base of
        # ``Optional[Union[A, B, C]]`` is satisfied by a target returning any one
        # of them, since a narrower return type is compatible with a wider
        # declared one. Taking ``[0]`` here silently bound the whole union to
        # whichever member happened to be written first.
        base_inners = [a for a in base_args if a is not type(None)]

        # Case 1: target is Optional[T]
        if _is_union_origin(target_origin) and type(None) in target_args:
            target_inners = [a for a in target_args if a is not type(None)]
            target_inner = (
                target_inners[0]
                if len(target_inners) == 1
                else Union[tuple(target_inners)]
            )
            return any(
                _is_return_compatible(base_inner, target_inner)
                for base_inner in base_inners
            )

        # Case 2: target is T → target can return T-only, still OK
        return any(
            _is_return_compatible(base_inner, target_ann) for base_inner in base_inners
        )

    # base: T, target: Optional[T] → NOT OK (target promises more cases).
    # Only reject when base is not *any* union; a union base (with or without
    # None) is decided by the union branches above/below, which handle TypeVar
    # options and non-None unions correctly.
    if (
        _is_union_origin(target_origin)
        and type(None) in target_args
        and not _is_union_origin(base_origin)
    ):
        return False

    # Handle non-optional Union
    if _is_union_origin(base_origin):
        return any(_is_return_compatible(opt, target_ann) for opt in base_args)

    # Awaitable[T]
    if base_origin is Awaitable:
        if target_origin is Awaitable:
            return True

    return _is_same_type(base_ann, target_ann)
