# API wrapper for Rez

from rez.resolved_context import ResolvedContext as env
from rez.packages_ import iter_packages as find
from rez.package_copy import copy_package
from rez.package_filter import Rule, PackageFilterList
from rez.package_repository import package_repository_manager
from rez.packages_ import Package
from rez.utils.formatting import PackageRequest
from rez.system import system
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


def find_one(name, range_=None, paths=None):
    return next(find(name, range_, paths))


def find_latest(name, range_=None, paths=None):
    it = find(name, range_)
    it = sorted(it, key=lambda pkg: pkg.version)

    try:
        return list(it)[-1]
    except IndexError:
        raise PackageNotFoundError(
            "package family not found: %s" % name
        )


try:
    from rez import __project__ as project
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
    "system",

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
