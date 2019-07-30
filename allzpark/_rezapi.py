# API wrapper for Rez

from rez.resolved_context import ResolvedContext as env
from rez.packages_ import iter_packages as find
from rez.package_copy import copy_package
from rez.package_filter import Rule, PackageFilterList
from rez.package_repository import package_repository_manager
from rez.packages_ import Package
from rez.utils.formatting import PackageRequest
from rez.config import config
from rez.util import which
from rez import __version__ as version
from rez.exceptions import (
    PackageFamilyNotFoundError,
    RexUndefinedVariableError,
    ResolvedContextError,
    RexError,
    PackageCommandError,
    PackageRequestError,
    PackageNotFoundError,
    RezError,
)
from rez.utils.graph_utils import save_graph


def clear_caches():
    for path in config.packages_path:
        repo = package_repository_manager.get_repository(path)
        repo.clear_caches()


def find_one(*args, **kwargs):
    return next(find(*args, **kwargs))


def find_latest(*args, **kwargs):
    return list(
        sorted(
            find(*args, **kwargs), key=lambda pkg: pkg.version
        )
    )[-1]


try:
    from rez import project
except ImportError:
    # nerdvegas/rez
    project = "rez"


__all__ = [
    "env",
    "find",
    "find_one",
    "find_latest",
    "config",
    "version",
    "project",
    "copy_package",
    "package_repository_manager",

    # Classes
    "Package",
    "PackageRequest",

    # Exceptions
    "PackageFamilyNotFoundError",
    "ResolvedContextError",
    "RexUndefinedVariableError",
    "RexError",
    "PackageCommandError",
    "PackageNotFoundError",
    "PackageRequestError",
    "RezError",

    # Filters
    "Rule",
    "PackageFilterList",

    # Extras
    "which",
    "save_graph",
    "clear_caches",
]
