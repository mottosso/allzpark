"""Command-line interface to allspark"""

import os
import sys
import time
import signal
import logging
import argparse
import contextlib

from .version import version
from . import allsparkconfig

timing = {}


def _load_userconfig(fname=None):
    fname = fname or os.getenv(
        "ALLSPARK_CONFIG_FILE",
        os.path.expanduser("~/allsparkconfig.py")
    )

    mod = {}
    with open(fname) as f:
        exec(compile(f.read(), f.name, 'exec'), mod)

    tell("- Loading custom allsparkconfig..")
    for key, value in mod.items():
        if key.startswith("__"):
            continue

        tell("  - %s=%r" % (key, value))
        setattr(allsparkconfig, key, value)


@contextlib.contextmanager
def timings(title, timing=True):
    sys.stdout.write(title)
    t0 = time.time()

    try:
        yield
    except Exception:
        sys.stdout.write("fail\n")
        raise
    else:
        if timing:
            sys.stdout.write("ok - %.2fs\n" % (time.time() - t0))
        else:
            sys.stdout.write("ok\n")


def tell(msg):
    sys.stdout.write("%s\n" % msg)


def main():
    parser = argparse.ArgumentParser("allspark", description=(
        "An application launcher built on Rez, "
        "pass --help for details"
    ))

    parser.add_argument("--verbose", action="store_true", help=(
        "Print additional information about Allspark during operation"))
    parser.add_argument("--version", action="store_true", help=(
        "Print version and exit"))
    parser.add_argument("--clear-settings", action="store_true", help=(
        "Start fresh with user preferences"))
    parser.add_argument("--config-file", type=str, help=(
        "Absolute path to allsparkconfig.py, takes precedence "
        "over ALLSPARK_CONFIG_FILE"))
    parser.add_argument("--no-config", action="store_true", help=(
        "Do not load custom allsparkconfig.py"))
    parser.add_argument("--root", help=(
        "Path to where projects live on disk, "
        "defaults to allsparkconfig.projects_dir"
    ))

    opts = parser.parse_args()

    if opts.version:
        tell(version)
        exit(0)

    print("=" * 30)
    print(" allspark (%s)" % version)
    print("=" * 30)

    with timings("- Loading Rez.. "):
        try:
            from rez import __file__ as _rez_location
            from rez.utils._version import _rez_version
            from rez.config import config
        except ImportError:
            tell("ERROR: allspark requires rez")
            exit(1)

    with timings("- Loading Qt.. "):
        try:
            from .vendor import Qt
        except ImportError:
            tell("ERROR: allspark requires a Python binding for Qt,\n"
                 "such as PySide, PySide2, PyQt4 or PyQt5.")
            exit(1)

        from .vendor import six
        from .vendor.Qt import QtWidgets, QtCore

    # Provide for vendor dependencies
    sys.modules["Qt"] = Qt
    sys.modules["six"] = six

    with timings("- Loading allspark.. "):
        from . import view, control, resources, util

    try:
        _load_userconfig(opts.config_file)
    except OSError:
        # That's OK
        pass

    logging.basicConfig(format=(
        "%(levelname)-8s %(name)s %(message)s" if opts.verbose else
        "%(message)s"
    ))
    logging.getLogger("allspark.vendor").setLevel(logging.CRITICAL)
    logging.getLogger("allspark").setLevel(logging.DEBUG
                                           if opts.verbose
                                           else logging.INFO)

    # Allow the application to die on CTRL+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    config.catch_rex_errors = False

    with timings("- Loading preferences.. "):
        storage = QtCore.QSettings(QtCore.QSettings.IniFormat,
                                   QtCore.QSettings.UserScope,
                                   "Allspark", "preferences")

        if opts.clear_settings:
            sys.stdout.write("(clean) ")
            storage.clear()

        defaults = {
            "memcachedURI": os.getenv("REZ_MEMCACHED_URI", "None"),
            "pythonExe": sys.executable,
            "pythonVersion": ".".join(map(str, sys.version_info)),
            "qtVersion": Qt.__binding_version__,
            "qtBinding": Qt.__binding__,
            "qtBindingVersion": Qt.__qt_version__,
            "rezLocation": os.path.dirname(_rez_location),
            "rezVersion": _rez_version,
            "rezConfigFile": os.getenv("REZ_CONFIG_FILE", "None"),
            "rezPackagesPath": config.packages_path,
            "rezLocalPath": config.local_packages_path.split(os.pathsep),
            "rezReleasePath": config.release_packages_path.split(os.pathsep),
            "settingsPath": storage.fileName(),
        }

        for key, value in defaults.items():
            storage.setValue(key, value)

        if allsparkconfig.startup_project:
            storage.setValue("startupProject", allsparkconfig.startup_project)

        if allsparkconfig.startup_application:
            storage.setValue("startupApp", allsparkconfig.startup_application)

    tell("-" * 30)  # Add some space between boot messages, and upcoming log

    app = QtWidgets.QApplication(sys.argv)
    ctrl = control.Controller(storage)

    def excepthook(type, value, traceback):
        """Try handling these from within the controller"""

        # Give handler a chance to remedy the situation
        handled = ctrl.on_unhandled_exception(type, value, traceback)

        if not handled:
            sys.__excepthook__(type, value, traceback)

    sys.excepthook = excepthook

    window = view.Window(ctrl)
    with open(resources.find("style.css")) as f:
        window.setStyleSheet(f.read())
    window.show()

    def measure():
        duration = time.time() - timing["beforeReset"]
        print("- Resolving contexts.. ok %.2fs" % duration)

    def init():
        timing["beforeReset"] = time.time()
        ctrl.reset(opts.root or allsparkconfig.projects_dir,
                   on_success=measure)

    # Give the window a moment to appear before occupying it
    QtCore.QTimer.singleShot(50, init)

    if os.name == "nt":
        util.windows_taskbar_compat()

    app.exec_()
