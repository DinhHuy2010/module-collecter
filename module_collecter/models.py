from importlib.machinery import ModuleSpec
from pathlib import Path

import attrs
from typing_extensions import Optional


@attrs.define(kw_only=True, frozen=True)
class ModuleInfo:
    fullname: str
    is_package: bool
    origin: Optional[Path]
    spec: ModuleSpec = attrs.field(repr=False)

    @classmethod
    def from_spec(cls, spec: ModuleSpec) -> "ModuleInfo":
        return cls(
            fullname=spec.name,
            is_package=spec.submodule_search_locations is not None,
            origin=Path(spec.origin) if spec.origin else None,
            spec=spec,
        )

@attrs.define(kw_only=True)
class ModuleCollecterResult:
    origin: ModuleInfo | None
    submodules: dict[str, ModuleInfo]

