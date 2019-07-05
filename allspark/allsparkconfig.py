"""The Allspark configuration file

Copy this onto your local drive and make modifications.
Anything not specified in your copy is inherited from here.

ALLSPARK_CONFIG_FILE=/path/to/allsparkconfig.py

"""


# Absolute path to where project packages reside
# Allspark uses this to establish a listing or available projects
projects_dir = "~/projects"

# Absolute path to where applicaion packages reside
# Allspark optionally uses this to enable the "Show all apps" button
applications_dir = None  # (optional)

# Load this project on startup.
# Defaults to the first available from `projects_dir`
startup_application = None  # (optional)

# Pre-select this application in the list of applications,
# if it exists in the startup project.
startup_project = None  # (optional)
