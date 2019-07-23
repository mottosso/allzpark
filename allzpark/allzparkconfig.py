"""The Allzpark configuration file

Copy this onto your local drive and make modifications.
Anything not specified in your copy is inherited from here.

ALLZPARK_CONFIG_FILE=/path/to/allzparkconfig.py

"""

import os as __os
import sys as __sys


# Default filter, editable via the Preferences page
exclude_filter = "*.beta"

# Where to go when clicking the logo
help_url = "https://allzpark.com"


def projects():
    """Return list of projects

    This function is called asynchronously, and is suitable
    for making complex filesystem or database queries.
    Can also be a variable of type tuple or list

    """

    try:
        return __os.listdir(__os.path.expanduser("~/projects"))
    except IOError:
        return ["No project"]


def applications():
    """Return list of applications

    Applications are typically provided by the project,
    this function is called when "Show all apps" is enabled.

    """

    return []


# Load this project on startup.
# Defaults to the first available from `projects_dir`
startup_application = None  # (optional)

# Pre-select this application in the list of applications,
# if it exists in the startup project.
startup_project = None  # (optional)


def applications_from_package(variant):
    """Return applications relative `variant`"""

    return list(
        str(req)
        for req in variant.requires
        if req.weak
    )


def metadata_from_package(variant):
    """Return metadata relative `variant`

    Blocking call, during change of project.

    IMPORTANT: this function must return at least the
        members part of the original function, else the program
        will not function. Very few safeguards are put in place
        in favour of performance.

    Arguments:
        variant (rez.packages_.Variant): Package from which to retrieve data

    Returns:
        dict: See function for values and types

    """

    data = getattr(variant, "_data", {})

    return dict(data, **{

        # Guaranteed keys, with default values
        "label": data.get("label", variant.name),
        "background": data.get("background"),
        "icon": data.get("icon", ""),
        "hidden": data.get("hidden", False),
    })


# Backup-copies of originals, with `_` prefix
# Useful for augmenting an existing value with your own config
__self__ = __sys.modules[__name__]
for member in dir(__self__):
    if member.startswith("__"):
        continue

    setattr(__self__, "_%s" % member, getattr(__self__, member))
