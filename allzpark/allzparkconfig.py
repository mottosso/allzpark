"""The Allzpark configuration file

Copy this onto your local drive and make modifications.
Anything not specified in your copy is inherited from here.

ALLZPARK_CONFIG_FILE=/path/to/allzparkconfig.py

"""

import os as __os


# Load this profile on startup.
# Defaults to the first available from `profiles`
startup_profile = ""  # (optional)

# Pre-select this application in the list of applications,
# if it exists in the startup profile.
startup_application = ""  # (optional)

# Default filter, editable via the Preferences page
exclude_filter = "*.beta"

# Where to go when clicking the logo
help_url = "https://allzpark.com"


def profiles():
    """Return list of profiles

    This function is called asynchronously, and is suitable
    for making complex filesystem or database queries.
    Can also be a variable of type tuple or list

    """

    try:
        return __os.listdir(__os.path.expanduser("~/profiles"))
    except IOError:
        return []


def applications():
    """Return list of applications

    Applications are typically provided by the profile,
    this function is called when "Show all apps" is enabled.

    """

    return []


def applications_from_package(variant):
    """Return applications relative `variant`

    Returns:
        list of strings: E.g. ['appA', 'appB==2019']

    """

    from . import _rezapi as rez

    # May not be defined
    requirements = variant.requires or []

    apps = list(
        str(req)
        for req in requirements
        if req.weak
    )

    # Strip the "weak" property of the request, else iter_packages
    # isn't able to find the requested versions.
    apps = [rez.PackageRequest(req.strip("~")) for req in apps]

    # Expand versions into their full range
    # E.g. maya-2018|2019 == ["maya-2018", "maya-2019"]
    flattened = list()
    for request in apps:
        flattened += rez.find(
            request.name,
            range_=request.range,
        )

    # Return strings
    apps = list(
        "%s==%s" % (package.name, package.version)
        for package in flattened
    )

    return apps


def metadata_from_package(variant):
    """Return metadata relative `variant`

    Blocking call, during change of profile.

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
