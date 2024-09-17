# pyright: strict

from __future__ import annotations

from collections import deque
from enum import Enum, auto
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_file_location
from pathlib import Path
from types import ModuleType

from more_itertools import always_iterable
from typing_extensions import Any, Callable, Generator

from module_collecter._vendor import module_utils
from module_collecter.models import ModuleInfo
from module_collecter.utils import contruct_name as _contruct_name
from module_collecter.utils import iterdir as _safe_iterdir


class EventVisitKind(Enum):
    START = auto()
    GOT_PACKAGE = auto()
    GOT_MODULE = auto()
    NOT_FOUND = auto()
    FINISH = auto()


def visit_all_spec(
    spec: ModuleSpec,
    *,
    level: int | None = None,
    verbose_callback: Callable[[EventVisitKind, dict[str, Any]], object] | None = None,
) -> Generator[ModuleInfo, None, None]:
    def _verbose_callback(event: EventVisitKind, data: dict[str, Any]) -> None: ...

    if verbose_callback is None:
        verbose_callback = _verbose_callback
        del _verbose_callback
    verbose_callback(EventVisitKind.START, {"spec": spec})
    stacks = deque([Path(ssp) for ssp in always_iterable(spec.submodule_search_locations)])
    while stacks:
        p = stacks.popleft()
        for item in _safe_iterdir(p):
            name = _contruct_name(spec, item)
            if item.is_file() and item.suffix == ".py":
                if level is not None and len(name.split(".")) - 1 > level:
                    continue
                cspec = spec_from_file_location(name, item)
                if cspec is None:
                    verbose_callback(EventVisitKind.NOT_FOUND, {"name": name, "item": item})
                else:
                    verbose_callback(EventVisitKind.GOT_MODULE, {"name": name, "item": item})
                    yield ModuleInfo.from_spec(cspec)
            elif item.is_dir():
                verbose_callback(EventVisitKind.GOT_PACKAGE, {"name": name, "item": item})
                stacks.append(item)
    verbose_callback(EventVisitKind.FINISH, {"spec": spec})


def walk_modules(
    spec: ModuleSpec | ModuleType | str,
    *,
    verbose_callback: Callable[[EventVisitKind, dict[str, Any]], object] | None = None,
    level: int | None = None,
) -> Generator[ModuleInfo, None, None]:
    resolved_spec = module_utils.module_spec(spec)
    if resolved_spec is None:
        return
    yield from visit_all_spec(resolved_spec, verbose_callback=verbose_callback, level=level)


def iter_modules(
    spec: ModuleSpec | ModuleType | str,
    *,
    verbose_callback: Callable[[EventVisitKind, dict[str, Any]], object] | None = None,
) -> Generator[ModuleInfo, None, None]:
    return walk_modules(spec, verbose_callback=verbose_callback, level=1)
