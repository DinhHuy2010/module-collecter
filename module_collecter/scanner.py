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
    def is_vaild_level(level: int | None, name: str) -> bool:
        return level is None or len(name[len(spec.name) :].split(".")) - 1 <= level

    if verbose_callback is None:
        verbose_callback = _verbose_callback
        del _verbose_callback
    verbose_callback(EventVisitKind.START, {"spec": spec})
    stacks = deque([Path(ssp) for ssp in always_iterable(spec.submodule_search_locations)])
    visited: set[str] = set()
    while stacks:
        current = stacks.popleft()
        pkg_init_file = current.joinpath("__init__.py")
        if pkg_init_file.is_file():
            name = _contruct_name(spec, pkg_init_file)
            if not is_vaild_level(level, name) or name in visited:
                continue

            cspec = spec_from_file_location(name, pkg_init_file)
            if cspec is not None:
                verbose_callback(EventVisitKind.GOT_PACKAGE, {"name": name, "item": current})
                yield ModuleInfo.from_spec(cspec)
            else:
                verbose_callback(EventVisitKind.NOT_FOUND, {"name": name, "item": current})
            visited.add(name)

        for item in _safe_iterdir(current):
            name = _contruct_name(spec, item)
            if item.is_file() and item.suffix == ".py" and name not in visited and is_vaild_level(level, name):
                cspec = spec_from_file_location(name, item)
                if cspec is not None:
                    verbose_callback(EventVisitKind.GOT_MODULE, {"name": name, "item": item})
                    yield ModuleInfo.from_spec(cspec)
                else:
                    verbose_callback(EventVisitKind.NOT_FOUND, {"name": name, "item": item})
                visited.add(name)
            elif item.is_dir() and item.stem != "__pycache__":
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
