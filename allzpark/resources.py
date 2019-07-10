import os
from .vendor.Qt import QtGui

dirname = os.path.dirname(__file__)
_cache = {}


def px(value, scale=1.0):
    return int(value * scale)


def find(*paths):
    fname = os.path.join(dirname, "resources", *paths)
    fname = os.path.normpath(fname)  # Conform slashes and backslashes
    return fname.replace("\\", "/")  # Cross-platform compatibility


def pixmap(*paths):
    path = find(*paths)
    basename = paths[-1]
    name, ext = os.path.splitext(basename)

    if not ext:
        path += ".png"

    try:
        pixmap = _cache[paths]
    except KeyError:
        pixmap = QtGui.QPixmap(find(*paths))
        _cache[paths] = pixmap

    return pixmap


def icon(*paths):
    return QtGui.QIcon(pixmap(*paths))
