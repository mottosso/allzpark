import os
from .vendor.Qt import QtGui

dirname = os.path.dirname(__file__)
_cache = {}


def px(value, scale=1.0):
    return value * scale


def find(*paths):
    return os.path.join(dirname, "resources", *paths)


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
