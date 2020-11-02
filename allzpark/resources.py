import os
import logging
from collections import OrderedDict as odict
from . import allzparkconfig
from .vendor.Qt import QtGui

dirname = os.path.dirname(__file__)
_cache = {}
_themes = odict()


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


def load_themes():
    _themes.clear()
    for theme in default_themes() + allzparkconfig.themes():
        _themes[theme["name"]] = theme


def theme_names():
    for name in _themes.keys():
        yield name


def load_theme(name=None):
    if name:
        theme = _themes.get(name)
        if theme is None:
            print("No theme named: %s" % name)
            return
    else:
        theme = next(iter(_themes.values()))

    source = theme["source"]
    keywords = theme.get("keywords", dict())

    if any(source.endswith(ext) for ext in [".css", ".qss"]):
        if not os.path.isfile(source):
            print("Theme stylesheet file not found: %s" % source)
            return
        else:
            with open(source) as f:
                css = f.read()
    else:
        # plain css code
        css = source

    _cache["_keywordsCache_"] = keywords
    _cache["_logColorCache_"] = {
        logging.DEBUG: keywords.get("log.debug", "lightgrey"),
        logging.INFO: keywords.get("log.info", "grey"),
        logging.WARNING: keywords.get("log.warning", "darkorange"),
        logging.ERROR: keywords.get("log.error", "lightcoral"),
        logging.CRITICAL: keywords.get("log.critical", "red"),
    }

    return format_stylesheet(css)


def format_stylesheet(css):
    try:
        return css % _cache["_keywordsCache_"]
    except KeyError as e:
        print("Stylesheet format failed: %s" % str(e))
        return ""


def log_level_color(level):
    log_colors = _cache.get("_logColorCache_", dict())
    return log_colors.get(level, "grey")


def default_themes():
    _load_fonts()
    res_root = os.path.join(dirname, "resources").replace("\\", "/")
    return [
        {
            "name": "default-dark",
            "source": find("style-dark.css"),
            "keywords": {
                "prim": "#2E2C2C",
                "brightest": "#403E3D",
                "bright": "#383635",
                "base": "#2E2C2C",
                "dim": "#21201F",
                "dimmest": "#141413",
                "hover": "rgba(104, 182, 237, 60)",
                "highlight": "rgb(110, 191, 245)",
                "highlighted": "#111111",
                "active": "silver",
                "inactive": "dimGray",
                "console": "#161616",
                "log.debug": "lightgrey",
                "log.info": "grey",
                "log.warning": "darkorange",
                "log.error": "lightcoral",
                "log.critical": "red",
                "res": res_root,
            }
        },
        {
            "name": "default-light",
            "source": find("style-light.css"),
            "keywords": {
                "prim": "#FFFFFF",
                "brightest": "#FDFDFD",
                "bright": "#F9F9F9",
                "base": "#EFEFEF",
                "dim": "#DFDFDF",
                "dimmest": "#CFCFCF",
                "hover": "rgba(122, 194, 245, 60)",
                "highlight": "rgb(136, 194, 235)",
                "highlighted": "#111111",
                "active": "black",
                "inactive": "gray",
                "console": "#363636",
                "log.debug": "lightgrey",
                "log.info": "grey",
                "log.warning": "darkorange",
                "log.error": "lightcoral",
                "log.critical": "red",
                "res": res_root,
            }
        },
    ]


def _load_fonts():
    """Load default fonts from resources"""
    _res_root = os.path.join(dirname, "resources").replace("\\", "/")

    font_root = os.path.join(_res_root, "fonts")
    fonts = [
        "opensans/OpenSans-Bold.ttf",
        "opensans/OpenSans-BoldItalic.ttf",
        "opensans/OpenSans-ExtraBold.ttf",
        "opensans/OpenSans-ExtraBoldItalic.ttf",
        "opensans/OpenSans-Italic.ttf",
        "opensans/OpenSans-Light.ttf",
        "opensans/OpenSans-LightItalic.ttf",
        "opensans/OpenSans-Regular.ttf",
        "opensans/OpenSans-Semibold.ttf",
        "opensans/OpenSans-SemiboldItalic.ttf",

        "jetbrainsmono/JetBrainsMono-Bold.ttf"
        "jetbrainsmono/JetBrainsMono-Bold-Italic.ttf"
        "jetbrainsmono/JetBrainsMono-ExtraBold.ttf"
        "jetbrainsmono/JetBrainsMono-ExtraBold-Italic.ttf"
        "jetbrainsmono/JetBrainsMono-ExtraLight.ttf"
        "jetbrainsmono/JetBrainsMono-ExtraLight-Italic.ttf"
        "jetbrainsmono/JetBrainsMono-Italic.ttf"
        "jetbrainsmono/JetBrainsMono-Light.ttf"
        "jetbrainsmono/JetBrainsMono-Light-Italic.ttf"
        "jetbrainsmono/JetBrainsMono-Medium.ttf"
        "jetbrainsmono/JetBrainsMono-Medium-Italic.ttf"
        "jetbrainsmono/JetBrainsMono-Regular.ttf"
        "jetbrainsmono/JetBrainsMono-SemiLight.ttf"
        "jetbrainsmono/JetBrainsMono-SemiLight-Italic.ttf"
    ]

    for font in fonts:
        path = os.path.join(font_root, font)
        QtGui.QFontDatabase.addApplicationFont(path)
