"""Collect submodules from a package."""

from .core import collect_modules
from .models import ModuleCollecterResult

__all__ = [
    "collect_modules",
    "ModuleCollecterResult"
]
