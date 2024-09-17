import sys
from contextlib import redirect_stdout
from importlib.machinery import ModuleSpec
from types import ModuleType

from typing_extensions import Any

from module_collecter._vendor.module_utils import get_module_name, module_spec
from module_collecter.models import ModuleCollecterResult, ModuleInfo
from module_collecter.scanner import EventVisitKind, visit_all_spec


def _collect_submodules(
    pkg: ModuleSpec | ModuleType | str, verbose: bool, level: int | None
) -> tuple[ModuleInfo | None, dict[str, ModuleInfo]]:
    submodules_count = 0
    submodules: dict[str, ModuleInfo] = {}
    spec = module_spec(pkg)
    rname = get_module_name(spec)
    if spec is None:
        return None, submodules

    def _verbose_handler(event: EventVisitKind, data: dict[str, Any]) -> None: # prgama: no cover
        nonlocal submodules_count
        with redirect_stdout(sys.stderr):
            if event is EventVisitKind.START:
                name = data["spec"].name
                print(f"start collecting {name!r}")
            elif event in {EventVisitKind.GOT_MODULE, EventVisitKind.GOT_PACKAGE}:
                name = data["name"]
                if name != spec.name:
                    item = data["item"]
                    print(f"got {name!r} at {item!r}")
                    submodules_count += 1
            elif event is EventVisitKind.NOT_FOUND:
                name = data["name"]
                item = data["item"]
                print(f"cannot found {name!r} at {item!r}")
            elif event is EventVisitKind.FINISH:
                name = data["spec"].name
                print(f"finish collecting {name!r}, collected {submodules_count} submodules")

    for info in visit_all_spec(spec, level=level, verbose_callback=(_verbose_handler if verbose is True else None)):
        submodules[info.fullname] = info
    root_module_info = submodules.pop(rname)
    return root_module_info, submodules


def collect_modules(
    pkg: ModuleType | ModuleSpec | str, /, *, verbose: bool = False, level: int | None = None
) -> ModuleCollecterResult:
    """Given a module object or a module spec or a string, returns the its submodules."""
    root_spec, subspeces = _collect_submodules(pkg, verbose, level)
    return ModuleCollecterResult(origin=root_spec, submodules=subspeces)
