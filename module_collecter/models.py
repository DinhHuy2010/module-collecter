from types import ModuleType

import attrs


@attrs.define(kw_only=True)
class ModuleCollecterResult:
    origin: ModuleType
    submodules: dict[str, ModuleType]
