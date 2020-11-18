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


def find_one(name, range_=None, paths=None, package_filter=None):
    """
    Find next package version

    Args:
        name (str): Name of the rez package
        range_ (VersionRange or str, optional): Limits versions to range
        paths (list of str, optional): Paths to search for packages
        package_filter (PackageFilter, optional): Limits versions to those
                                                  that match package filter

    Returns:
        rez.packages_.Package
    """
    if package_filter:
        return next(package_filter.iter_packages(name, range_, paths))
    else:
        return next(find(name, range_, paths))


def find_latest(name, range_=None, paths=None, package_filter=None):
    """
    Find latest package version

    Args:
        name (str): Name of the rez package
        range_ (VersionRange or str, optional): Limits versions to range
        paths (list of str, optional): Paths to search for packages
        package_filter (PackageFilter, optional): Limits versions to those
                                                  that match package filter

    Returns:
        rez.packages_.Package
    """
    if package_filter:
        it = package_filter.iter_packages(name, range_, paths)
    else:
        it = find(name, range_, paths)

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
