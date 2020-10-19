"""Version includes the Git revision number

This module separates between deployed and development versions of allzpark.
A development version draws its minor version directly from Git, the total
number of commits on the current branch equals the revision number. Once
deployed, this number is embedded into the Python package.

"""

version = "1.3"

try:
    # Look for serialised version
    from .__version__ import version

except ImportError:
    # Else, we're likely running out of a Git repository
    import os as _os
    import subprocess as _subprocess

    try:
        # If used as a git repository
        _cwd = _os.path.dirname(__file__)
        _patch = int(_subprocess.check_output(
            ["git", "rev-list", "HEAD", "--count"],

            cwd=_cwd,

            # Ensure strings are returned from both Python 2 and 3
            universal_newlines=True,

        ).rstrip())

        # Builds since previous minor version
        _patch -= 323

    except Exception:
        # Otherwise, no big deal
        pass

    else:
        version += ".%s" % _patch
