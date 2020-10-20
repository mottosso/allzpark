import os
from . import allzparkconfig
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


def load_style(palette_name, load_fonts=False):
    palettes = load_palettes()
    _cache["_current_palette_"] = palettes[palette_name]

    with open(find("style.css")) as f:
        css = format_stylesheet(f.read())

    if load_fonts:
        _load_fonts()

    return css


def format_stylesheet(css):
    return css % dict(
        root=dirname.replace("\\", "/"),
        res=os.path.join(dirname, "resources").replace("\\", "/"),
        **_cache["_current_palette_"]
    )


def load_palettes():
    palettes = {
        "dark": {
            "brightest": "#403E3D",
            "bright": "#383635",
            "base": "#2E2C2C",
            "dim": "#21201F",
            "dimmest": "#141413",

            "hover": "rgba(65, 166, 148, 40)",
            "highlight": "rgb(117, 189, 176)",
            "highlighted": "#111111",
            "active": "silver",
            "inactive": "dimGray",
        },

        "light": {
            "brightest": "#fafcfe",
            "bright": "#efeff0",
            "base": "#e6e6e6",
            "dim": "#c5c7c9",
            "dimmest": "#b2b5b8",

            "hover": "rgba(57, 196, 171, 40)",
            "highlight": "rgb(105, 214, 194)",
            "highlighted": "#111111",
            "active": "black",
            "inactive": "gray",
        },
    }
    if allzparkconfig.palettes:
        palettes.update(allzparkconfig.palettes)

    return palettes


def _load_fonts():
    """Load fonts from resources"""
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
