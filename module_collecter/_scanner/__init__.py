# pyright: strict

from __future__ import annotations

from collections import deque
from importlib.machinery import ModuleSpec
from importlib.util import spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import (
    Callable,
    Generator,
    Optional,
)

import attrs
from more_itertools import always_iterable

from package_scanner._vendor import module_utils
from package_scanner.utils import iterdir as _safe_iterdir
from package_scanner.utils import contruct_name as _contruct_name


@attrs.define(kw_only=True, frozen=True)
class ModuleInfo:
    fullname: str
    is_package: bool
    origin: Optional[Path]
    spec: ModuleSpec = attrs.field(repr=False)

    @classmethod
    def from_spec(cls, spec: ModuleSpec) -> ModuleInfo:
        return cls(
            fullname=spec.name,
            is_package=spec.submodule_search_locations is not None,
            origin=Path(spec.origin) if spec.origin else None,
            spec=spec,
        )


def _visit_all_spec(
    spec: ModuleSpec,
    *,
    on_spec_not_found: Callable[[str, Path], object] | None = None,
    level: int | None = None,
) -> Generator[ModuleInfo, None, None]:
    stacks = deque(
        [Path(ssp) for ssp in always_iterable(spec.submodule_search_locations)]
    )
    while stacks:
        p = stacks.popleft()
        for item in _safe_iterdir(p):
            if item.is_file() and item.suffix == ".py":
                name = _contruct_name(spec, item)
                if level is not None and len(name.split(".")) - 1 > level:
                    continue
                cspec = spec_from_file_location(name, item)
                if cspec is None:
                    if on_spec_not_found is not None:
                        on_spec_not_found(name, item)
                else:
                    yield ModuleInfo.from_spec(cspec)
            elif item.is_dir():
                stacks.append(item)


def walk_modules(
    spec: ModuleSpec | ModuleType | str,
    *,
    on_spec_not_found: Callable[[str, Path], object] | None = None,
    level: int | None = None,
) -> Generator[ModuleInfo, None, None]:
    resolved_spec = module_utils.module_spec(spec)
    if resolved_spec is None:
        return
    yield from _visit_all_spec(
        resolved_spec, on_spec_not_found=on_spec_not_found, level=level
    )


def iter_modules(
    spec: ModuleSpec | ModuleType | str,
    *,
    on_spec_not_found: Callable[[str, Path], object] | None = None,
) -> Generator[ModuleInfo, None, None]:
    return walk_modules(spec, on_spec_not_found=on_spec_not_found, level=1)


