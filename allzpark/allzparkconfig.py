"""The Allzpark configuration file

Copy this onto your local drive and make modifications.
Anything not specified in your copy is inherited from here.

ALLZPARK_CONFIG_FILE=/path/to/allzparkconfig.py

"""

import os


def projects():
    """Return list of projects

    This function is called asynchronously, and is suitable
    for making complex filesystem or database queries.
    Can also be a variable of type tuple or list

    """

    return os.listdir("~/projects")


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
