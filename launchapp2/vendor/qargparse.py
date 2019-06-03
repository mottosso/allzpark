import re
import logging

from collections import OrderedDict as odict
from Qt import QtCore, QtWidgets

__version__ = "0.5.0"
_log = logging.getLogger(__name__)
_type = type


class QArgumentParser(QtWidgets.QWidget):
    """User interface arguments

    Arguments:
        arguments (list, optional): Instances of QArgument
        description (str, optional): Long-form text of what this parser is for
        storage (QSettings, optional): Persistence to disk, providing
            value() and setValue() methods

    """

    changed = QtCore.Signal(QtCore.QObject)  # A QArgument

    def __init__(self,
                 arguments=None,
                 description=None,
                 storage=None,
                 parent=None):
        super(QArgumentParser, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)

        # Create internal settings
        if storage is True:
            storage = QtCore.QSettings(
                QtCore.QSettings.IniFormat,
                QtCore.QSettings.UserScope,
                __name__, "QArgparse",
            )

        if storage is not None:
            _log.info("Storing settings @ %s" % storage.fileName())

        arguments = arguments or []
        description = QtWidgets.QLabel(description or "")

        assert hasattr(arguments, "__iter__"), "arguments must be iterable"
        assert isinstance(storage, (type(None), QtCore.QSettings)), (
            "storage must be of type QSettings"
        )

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(description, 0, 0, 1, 2)
        layout.setRowStretch(999, 1)

        self._row = 1
        self._storage = storage
        self._arguments = odict()
        self._desciption = description

        for arg in arguments or []:
            self._addArgument(arg)

        self.setStyleSheet(style)

    def setDescription(self, text):
        self._desciption.setText(text)

    def addArgument(self, name, type=None, default=None, **kwargs):
        # Infer type from default
        if type is None and default is not None:
            type = _type(default)

        # Default to string
        type = type or str

        Argument = {
            None: String,
            int: Integer,
            float: Float,
            bool: Boolean,
            str: String,
            list: Enum,
            tuple: Enum,
        }.get(type, type)

        arg = Argument(name, default=default, **kwargs)
        self._addArgument(arg)
        return arg

    def _addArgument(self, arg):
        if arg["name"] in self._arguments:
            raise ValueError("Duplicate argument '%s'" % arg["name"])

        if self._storage is not None:
            arg["default"] = self._storage.value(arg["name"]) or arg["default"]

        arg.changed.connect(lambda: self.changed.emit(arg))

        layout = self.layout()
        c0, c1 = arg.create()

        for widget in (c0, c1):
            widget.setToolTip(arg["help"])
            widget.setObjectName(arg["name"])  # useful in CSS
            widget.setProperty("type", type(arg).__name__)
            widget.setAttribute(QtCore.Qt.WA_StyledBackground)

        layout.addWidget(c0, self._row, 0, QtCore.Qt.AlignTop)
        layout.addWidget(c1, self._row, 1)

        self._row += 1
        self._arguments[arg["name"]] = arg

    def clear(self):
        assert self._storage, "Cannot clear without persistent storage"
        self._storage.clear()
        _log.info("Clearing settings @ %s" % self._storage.fileName())

    def find(self, name):
        return self._arguments[name]

    # Optional PEP08 syntax
    add_argument = addArgument


class QArgument(QtCore.QObject):
    changed = QtCore.Signal()

    def __init__(self, name, **kwargs):
        super(QArgument, self).__init__(kwargs.pop("parent", None))

        kwargs["name"] = name
        kwargs["label"] = kwargs.get("label", self.camelToTitle(name))
        kwargs["default"] = kwargs.get("default", None)
        kwargs["help"] = kwargs.get("help", "")
        kwargs["read"] = kwargs.get("read")
        kwargs["write"] = kwargs.get("write")

        self._data = kwargs

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def create(self):
        return QtWidgets.QLabel(), QtWidgets.QWidget()

    def read(self):
        pass

    def write(self, value):
        pass

    def camelToTitle(self, text):
        """Convert camelCase `text` to Title Case

        Example:
            >>> camelToTitle("mixedCase")
            "Mixed Case"
            >>> camelToTitle("myName")
            "My Name"
            >>> camelToTitle("you")
            "You"
            >>> camelToTitle("You")
            "You"
            >>> camelToTitle("This is That")
            "This Is That"

        """

        return re.sub(
            r"((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))",
            r" \1", text
        ).title()

    camel_to_title = camelToTitle


class Boolean(QArgument):
    def create(self):
        label = QtWidgets.QLabel(self["label"])
        widget = QtWidgets.QCheckBox()
        widget.clicked.connect(self.changed.emit)

        if isinstance(self, Tristate):
            self.read = lambda: widget.checkState()
            state = {
                0: QtCore.Qt.Unchecked,
                1: QtCore.Qt.PartiallyChecked,
                2: QtCore.Qt.Checked,
                "1": QtCore.Qt.PartiallyChecked,
                "0": QtCore.Qt.Unchecked,
                "2": QtCore.Qt.Checked,
            }
        else:
            self.read = lambda: bool(widget.checkState())
            state = {
                0: QtCore.Qt.Unchecked,
                1: QtCore.Qt.Checked,

                # May be stored as string, if used with QSettings(..IniFormat)
                "false": QtCore.Qt.Unchecked,
                "true": QtCore.Qt.Checked,
            }

        self.write = lambda value: widget.setCheckState(state[value])

        if self["default"] is not None:
            self.write(self["default"])

        return label, widget


class Tristate(QArgument):
    pass


class Number(QArgument):
    def create(self):
        label = QtWidgets.QLabel(self["label"])

        if isinstance(self, Float):
            widget = QtWidgets.QDoubleSpinBox()
        else:
            widget = QtWidgets.QSpinBox()

        widget.editingFinished.connect(self.changed.emit)
        self.read = lambda: widget.value()
        self.write = lambda value: widget.setValue(value)

        if self["default"] is not None:
            self.write(self["default"])

        return label, widget


class Integer(Number):
    pass


class Float(Number):
    pass


class Range(Number):
    pass


class String(QArgument):
    def create(self):
        label = QtWidgets.QLabel(self["label"])
        widget = QtWidgets.QLineEdit()
        widget.editingFinished.connect(self.changed.emit)
        self.read = lambda: widget.text()
        self.write = lambda value: widget.setText(value)

        if isinstance(self, Info):
            widget.setReadOnly(True)

        if self["default"] is not None:
            self.write(self["default"])

        return label, widget


class Info(String):
    pass


class Color(String):
    pass


class Button(QArgument):
    def create(self):
        label = QtWidgets.QLabel()
        widget = QtWidgets.QPushButton(self["label"])
        widget.clicked.connect(self.changed.emit)

        state = [
            QtCore.Qt.Unchecked,
            QtCore.Qt.Checked,
        ]

        if isinstance(self, Toggle):
            widget.setCheckable(True)
            self.read = lambda: widget.checkState()
            self.write = (
                lambda value: widget.setCheckState(state[int(value)])
            )
        else:
            self.read = lambda: "clicked"
            self.write = lambda value: None

        if self["default"] is not None:
            self.write(self["default"])

        return label, widget


class Toggle(Button):
    pass


class List(QArgument):
    def __init__(self, name, **kwargs):
        kwargs["items"] = kwargs.get("items", ["No items"])
        super(List, self).__init__(name, **kwargs)

    def create(self):
        label = QtWidgets.QLabel(self["name"])
        label.setAlignment(QtCore.Qt.AlignBottom)

        def on_edited(topleft, bottomright, roles=None):
            self.changed.emit()

        class Model(QtCore.QStringListModel):
            def data(self, index, role):
                return super(Model, self).data(index, role)

        model = QtCore.QStringListModel(self["items"] + [""])
        model.dataChanged.connect(on_edited)
        widget = QtWidgets.QListView()
        widget.setModel(model)

        self.read = lambda: model.stringList()
        self.write = lambda value: model.setStringList(value)

        return label, widget


class Separator(QArgument):
    """Visual separator

    Example:

        item1
        item2
        ------------
        item3
        item4

    """

    def create(self):
        label = QtWidgets.QLabel(self["name"])
        label.setAlignment(QtCore.Qt.AlignBottom)
        widget = QtWidgets.QWidget()

        self.read = lambda: None
        self.write = lambda value: None

        return label, widget


class Enum(QArgument):
    def __init__(self, name, **kwargs):
        kwargs["default"] = kwargs.get("default", 0)
        kwargs["items"] = kwargs.get("items", [])

        assert isinstance(kwargs["items"], (tuple, list)), (
            "items must be list"
        )

        super(Enum, self).__init__(name, **kwargs)

    def create(self):
        label = QtWidgets.QLabel(self["name"])
        widget = QtWidgets.QComboBox()
        widget.addItems(self["items"])
        widget.currentIndexChanged.connect(
            lambda index: self.changed.emit())

        self.read = lambda: widget.currentText()
        self.write = lambda value: widget.setCurrentIndex(value)

        if self["default"] is not None:
            self.write(self["default"])

        return label, widget


style = """\

*[type="Button"] {
    text-align:left;
}

*[type="Info"] {
    background: transparent;
    border: none;
}

QLabel[type="Separator"] {
    min-height: 20px;
    text-decoration: underline;
}

"""


def _demo():
    import sys
    app = QtWidgets.QApplication(sys.argv)

    parser = QArgumentParser()
    parser.setWindowTitle("Demo")
    parser.setMinimumWidth(300)

    parser.add_argument("name", default="Marcus", help="Your name")
    parser.add_argument("age", default=33, help="Your age")
    parser.add_argument("height", default=1.87, help="Your height")
    parser.add_argument("alive", default=True, help="Your state")
    parser.add_argument("class", type=Enum, items=[
        "Ranger",
        "Warrior",
        "Sorcerer",
        "Monk",
    ], default=2, help="Your class")

    parser.add_argument("options", type=Separator)
    parser.add_argument("paths", type=List, items=[
        "Value A",
        "Value B",
        "Some other value",
        "And finally, value C",
    ])

    parser.show()
    app.exec_()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--demo", action="store_true")

    opts = parser.parse_args()

    if opts.demo:
        _demo()

    if opts.version:
        print(__version__)
