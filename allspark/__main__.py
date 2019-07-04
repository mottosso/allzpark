import os
import sys
import time
from . import cli

# Debugging, measure start-up time
# NOTE: Handle this prior to importing anything
if os.getenv("ALLSPARK_STARTTIME"):

    try:
        t0 = float(os.getenv("ALLSPARK_STARTTIME"))
        t1 = time.time()

    except ValueError:
        raise ValueError(
            "ALLSPARK_STARTTIME must be in format time.time()"
        )

    duration = t1 - t0
    print("shell to python: %.2f s" % duration)

sys.exit(cli.main())
