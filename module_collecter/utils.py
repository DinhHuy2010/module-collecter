# pyright: strict

from __future__ import annotations

from functools import partial
from importlib.machinery import ModuleSpec
from os import fsdecode
from pathlib import Path

from more_itertools import always_iterable, iter_except
from typing_extensions import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath


def contruct_name(root_spec: ModuleSpec, path: Path) -> str:
    if root_spec.origin is not None:
        pparts = Path(root_spec.origin).parent.parts
    else:
        pparts = Path(next(always_iterable(root_spec.submodule_search_locations))).parts
    parts = [root_spec.name]
    parts.extend(path.parts[len(pparts) : -1])
    if path.stem != "__init__":
        parts.append(path.stem)
    return ".".join(parts)


def iterdir(path: "StrOrBytesPath") -> Iterator[Path]:
    path = Path(fsdecode(path))
    return iter_except(partial(next, path.iterdir()), (OSError, StopIteration))
