"""Collect submodules from a package."""

from module_collecter.core import collect_modules
from module_collecter.models import ModuleCollecterResult

__all__ = [
    "collect_modules",
    "ModuleCollecterResult"
]
