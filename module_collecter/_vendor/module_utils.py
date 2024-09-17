# pyright: strict

import importlib
import importlib.machinery
import inspect
import os
import sys
import sysconfig
from enum import Flag, auto
from importlib.machinery import ModuleSpec
from importlib.util import find_spec
from pathlib import Path
from types import ModuleType

from typing_extensions import Any, Optional, TypeVar, deprecated

T = TypeVar("T")

__all__: list[str]


class ModuleLocationKind(Flag):
    NORMAL_BUILTIN = auto()
    FROZEN = auto()
    EXTENSION = auto()
    STDLIB = auto()
    SITE_PACKAGES = auto()
    LOCAL = auto()
    BUILTIN = NORMAL_BUILTIN | FROZEN | EXTENSION


_INTERACTIVE_DEFAULT_NAME = "<interactive-repl>"
_RUN_DIRECTLY_NAME = "<from-direct>"
_FALLBACK_DEFAULT_NAME = "<unkhown-module>"
_SPECIAL_NAMES = {_INTERACTIVE_DEFAULT_NAME, _RUN_DIRECTLY_NAME}

_MODULE_LOCATION_KIND_CACHE: dict[str, ModuleLocationKind] = {}


def _get_python_lib_folder_name() -> str:
    if os.name == "nt":  # noqa: SIM108
        libdirname = "Lib"
    else:
        libdirname = f"lib/python{sys.version_info.major}.{sys.version_info.minor}"
    return libdirname


def _getmodname_from_source(src: Any) -> Optional[str]:
    try:
        fn = inspect.getfile(src)
    except (TypeError, OSError):
        return None
    if fn == "<string>":
        return _RUN_DIRECTLY_NAME
    if fn == "<stdin>":
        return _INTERACTIVE_DEFAULT_NAME
    return inspect.getmodulename(fn)


def _get_module_name(  # noqa: PLR0911
    name_or_mod: str | ModuleSpec | ModuleType,
    handle_main: bool = True,
    from_frame: bool = False,
) -> Optional[str]:
    if isinstance(name_or_mod, ModuleSpec):
        return name_or_mod.name
    elif isinstance(name_or_mod, ModuleType):
        return _getmodname_from_source(name_or_mod)
    else:
        if name_or_mod == "__main__" and handle_main is False:
            return name_or_mod
        if name_or_mod in _SPECIAL_NAMES and from_frame is True:
            return name_or_mod
        module = sys.modules.get(name_or_mod)
        if module is not None:
            return _getmodname_from_source(module)
        else:
            try:
                spec = find_spec(name_or_mod)
            except ValueError:
                return None
            else:
                if spec:
                    return spec.name
                return None


def _get_spec(obj: str | ModuleSpec | ModuleType) -> Optional[ModuleSpec]:
    if isinstance(obj, ModuleSpec):
        spec = obj
    elif isinstance(obj, ModuleType):
        spec = obj.__spec__
    else:
        try:
            spec = find_spec(obj)
        except ValueError:
            if obj != "__main__":
                return None
            name = _get_module_name(obj)
            if name is None:
                return None
            spec = find_spec(name)
        except Exception:
            return None
    return spec


def _get_root_module(name: str) -> str:
    parts = name.split(".")
    if not parts:
        raise ValueError("name is empty")
    return parts[0]


def _push_cache(name: str, result: ModuleLocationKind) -> ModuleLocationKind:
    _MODULE_LOCATION_KIND_CACHE[name] = result
    return result


def _path_startswith(a: Path, b: Path) -> bool:
    return a.parts[: len(b.parts)] == b.parts


def _determine_entry(mf: str, sitepackages: set[Path]) -> ModuleLocationKind | None:  # noqa: PLR0911
    if mf == "frozen":
        return ModuleLocationKind.FROZEN
    try:
        f = Path(mf).resolve(strict=True)
    except Exception:
        return None

    if f.suffix in importlib.machinery.EXTENSION_SUFFIXES:
        return ModuleLocationKind.EXTENSION

    if _path_startswith(f, get_python_stdlib_path()):
        return ModuleLocationKind.STDLIB

    for sp in sitepackages:
        if _path_startswith(f, sp):
            return ModuleLocationKind.SITE_PACKAGES

    cwd = Path.cwd().resolve(strict=True)
    if _path_startswith(f, cwd):
        return ModuleLocationKind.LOCAL

    return None


@deprecated("Use get_python_stdlib_path", category=DeprecationWarning)
def get_python_stdlib_location() -> Path:
    return Path(sys.base_prefix, _get_python_lib_folder_name())


def get_python_stdlib_path() -> Path:
    return Path(sysconfig.get_path("stdlib"))


def get_python_platstdlib_path() -> Path:
    return Path(sysconfig.get_path("platstdlib"))


def get_python_sitepackages() -> Path:
    return get_python_platstdlib_path().joinpath("site-packages")


def get_python_system_sitepackages() -> Path:
    return get_python_stdlib_path().joinpath("site-packages")


def get_python_nonlocal_lib_paths(
    *, include_system_site_package: bool = False
) -> list[Path]:
    paths = {get_python_stdlib_path()}
    if include_system_site_package:
        paths.add(get_python_system_sitepackages())
    paths.update({get_python_platstdlib_path(), get_python_sitepackages()})

    return sorted(paths)


def module_spec(name_or_mod: str | ModuleSpec | ModuleType) -> Optional[ModuleSpec]:
    return _get_spec(name_or_mod)


def where_module_from(
    name_or_mod: str | ModuleType | ModuleSpec,
    *,
    include_system_sitepackages: bool = False,
) -> ModuleLocationKind | None:
    spec = _get_spec(name_or_mod)
    if spec is None:
        return None
    module_name = _get_root_module(spec.name)
    if module_name in _MODULE_LOCATION_KIND_CACHE:
        return _MODULE_LOCATION_KIND_CACHE[module_name]
    elif module_name in sys.builtin_module_names:
        return _push_cache(module_name, ModuleLocationKind.NORMAL_BUILTIN)

    __module_file__ = spec.origin
    if not __module_file__:
        return None

    sitepackages = {get_python_sitepackages()}
    if include_system_sitepackages:
        sitepackages.add(get_python_system_sitepackages())
    entry = _determine_entry(__module_file__, sitepackages)
    if entry is None:
        return None

    return _push_cache(module_name, entry)


def is_module_builtin(name_or_mod: str | ModuleType | ModuleSpec) -> bool:
    wmf = where_module_from(name_or_mod)
    return wmf is not None and wmf in ModuleLocationKind.BUILTIN


def is_module_local(name_or_mod: str | ModuleType | ModuleSpec) -> bool:
    wmf = where_module_from(name_or_mod)
    return wmf is not None and wmf is ModuleLocationKind.LOCAL


def get_module_name(
    name_or_mod: Optional[str | ModuleSpec | ModuleType] = None,
    *,
    handle_main: bool = True,
    default_module_name: str = _FALLBACK_DEFAULT_NAME,
) -> str:
    from_frame = False
    if name_or_mod is None:
        source = inspect.currentframe()

        # Move to the caller's frame
        if source is None:
            return default_module_name
        source = source.f_back
        if source is None:
            return default_module_name
        name = _getmodname_from_source(source)
        if name is None:
            return default_module_name
        name_or_mod = name
        from_frame = True

    return _get_module_name(name_or_mod, handle_main, from_frame) or default_module_name
