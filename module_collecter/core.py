from contextlib import redirect_stderr, redirect_stdout
from importlib import import_module
from io import StringIO
from pkgutil import walk_packages
from traceback import print_exception
from types import ModuleType

from .models import ModuleCollecterResult


def _collect_submodules(pkg, verbose):
    modules = {}
    for info in walk_packages(
        getattr(pkg, "__path__", []),
        prefix=f"{pkg.__name__}.",
        onerror=lambda error: ...,
    ):
        try:
            f = StringIO()
            with redirect_stdout(f), redirect_stderr(f):
                mod = import_module(info.name)
        except BaseException as exc:
            if verbose:
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    continue
                print(f"error during import {info.name!r}:")
                print_exception(exc)
            continue
        modules[info.name] = mod
    return modules


def collect_modules(
    pkg: ModuleType, /, *, verbose: bool = False
) -> ModuleCollecterResult:
    """Given a module object, returns the its submodules."""
    return ModuleCollecterResult(
        origin=pkg, submodules=_collect_submodules(pkg, verbose)
    )
