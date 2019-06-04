import os as _os
import subprocess as _subprocess

try:
    # If used as a git repository
    _cwd = _os.path.dirname(__file__)
    build = int(_subprocess.check_output(
        "git rev-list HEAD --count", cwd=_cwd,

        # Ensure strings are returned from both Python 2 and 3
        universal_newlines=True

    ).rstrip())
except Exception as e:
    # Otherwise, no big deal
    build = 0

version = "1.0.2" + ("-build%s" % build) if build else ""
