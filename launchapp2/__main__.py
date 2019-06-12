"""Command-line interface to launchapp2"""

import os
import sys
import signal
import logging
import argparse

from .version import version


# These can be overridden
defaults = {
    "REZ_PACKAGES_PATH": os.path.join(os.path.expanduser("~/packages")),

    # Without this, resolving contexts may take seconds to minutes
    "REZ_MEMCACHED_URI": "127.0.0.1:11211",

    # Defaults to finding projects in your home directory
    "LAUNCHAPP_ROOT": os.path.join(os.path.expanduser("~/projects")),
}

for key, default in defaults.items():
    os.environ[key] = os.getenv(key, default)


def tell(msg):
    print("%s" % msg)


parser = argparse.ArgumentParser("launchapp 2.0", description=(
    "An application launcher built on Rez, "
    "pass --help for details"
))

parser.add_argument("--verbose", action="store_true")
parser.add_argument("--version", action="store_true")
parser.add_argument("--clear-settings", action="store_true")
parser.add_argument("--startup-project")
parser.add_argument("--root",
                    default=os.environ["LAUNCHAPP_ROOT"],
                    help="Path to where projects live on disk, "
                         "defaults to LAUNCHAPP_ROOT")

opts = parser.parse_args()

if opts.version:
    tell(version)
    exit(0)

print("=" * 30)
print(" launchapp2 (%s)" % version)
print("=" * 30)

tell("- Loading Rez..")

try:
    from rez import __file__ as _rez_location
    from rez.utils._version import _rez_version
    from rez.config import config
except ImportError:
    tell("ERROR: launchapp2 requires rez")
    exit(1)

tell("- Loading Qt..")

try:
    from .vendor import Qt
except ImportError:
    tell("ERROR: launchapp2 requires a Python binding for Qt,\n"
         "such as PySide, PySide2, PyQt4 or PyQt5.")
    exit(1)

from .vendor import six
from .vendor.Qt import QtWidgets, QtCore

# Provide for vendor dependencies
sys.modules["Qt"] = Qt
sys.modules["six"] = six

tell("- Loading launchapp2..")

from . import view, control, resources, util

logging.basicConfig(format=(
    "%(levelname)-8s %(name)s %(message)s" if opts.verbose else
    "%(message)s"
))
logging.getLogger("launchapp2.vendor").setLevel(logging.CRITICAL)
logging.getLogger("launchapp2").setLevel(logging.DEBUG
                                         if opts.verbose
                                         else logging.INFO)


# Allow the application to die on CTRL+C
signal.signal(signal.SIGINT, signal.SIG_DFL)

config.catch_rex_errors = False

storage = QtCore.QSettings(QtCore.QSettings.IniFormat,
                           QtCore.QSettings.UserScope,
                           "Anima", "launchapp2")

defaults = {
    "memcachedURI": os.getenv("REZ_MEMCACHED_URI", "None"),
    "pythonExe": sys.executable,
    "pythonVersion": ".".join(map(str, sys.version_info)),
    "qtVersion": Qt.__binding_version__,
    "qtBinding": Qt.__binding__,
    "qtBindingVersion": Qt.__qt_version__,
    "rezLocation": os.path.dirname(_rez_location),
    "rezVersion": _rez_version,
    "rezPackagesPath": config.packages_path,
    "rezLocalPath": config.local_packages_path.split(os.pathsep),
    "rezReleasePath": config.release_packages_path.split(os.pathsep),
    "settingsPath": storage.fileName(),
}

for key, value in defaults.items():
    storage.setValue(key, value)


if opts.clear_settings:
    tell("Clearing settings..")
    storage.clear()

if opts.startup_project:
    storage.setValue("startupProject", opts.startup_project)

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


def init():
    tell("Resetting..")
    ctrl.reset(opts.root)


# Give the window a moment to appear before occupying it
QtCore.QTimer.singleShot(50, init)

if os.name == "nt":
    util.windows_taskbar_compat()

app.exec_()
