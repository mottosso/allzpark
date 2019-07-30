import os
import time

# Debugging, measure start-up time
# NOTE: Handle this prior to importing anything
if os.getenv("ALLZPARK_STARTTIME"):

    try:
        t0 = float(os.getenv("ALLZPARK_STARTTIME"))
        t1 = time.time()

    except ValueError:
        raise ValueError(
            "ALLZPARK_STARTTIME must be in format time.time()"
        )

    duration = t1 - t0
    print("shell to python: %.2f s" % duration)


import sys
from . import cli
sys.exit(cli.main())
