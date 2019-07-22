from .vendor.Qt import QtWidgets, QtCore, QtCompat, IsPySide2, IsPyQt5
from . import model as model_


class Version(object):
    def __init__(self, delegate):
        self._delegate = delegate
        self._mapper = None

    def createEditor(self, parent, option, index):
        if index.column() != 1:
            return

        model = index.model()
        item = index.internalPointer()

        # Query promise to trigger an update of children
        index = model.createIndex(0, 0, item.child(0))
        promise = index.data(model_.DisplayRole)

        editor = QtWidgets.QComboBox(parent)
        editor.addItem(promise)
        editor.setFocusPolicy(QtCore.Qt.StrongFocus)

        def finish():
            if QtCompat.isValid(editor):
                editor.close()
            model.promiseFulfilled.disconnect(finish)

        if IsPySide2 or IsPyQt5:
            model.promiseFulfilled.connect(finish)

        return editor

    def setEditorData(self, editor, index):
        item = index.internalPointer()
        current = index.data(model_.DisplayRole)

        editor.clear()
        children = item.children()
        for index, child in enumerate(children):
            option = child[model_.DisplayRole][0]
            editor.addItem(option)

            if option == current:
                editor.setCurrentIndex(index)

    def setModelData(self, editor, model, index):
        model = index.model()
        version = editor.currentText()
        item = index.internalPointer()
        current = index.data(model_.DisplayRole)
        default = index.data(model_.DefaultRole)

        for child in item.children():
            option = child[model_.DisplayRole][0]

            # Ensure selected option exists
            if version != option:
                continue

            if version != current:
                model.setData(index, version, model_.DisplayRole)

                font = editor.font()
                font.setBold(version != default)

                model.setData(index, font, QtCore.Qt.FontRole)


class DelegateProxy(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(DelegateProxy, self).__init__(parent)

        types = {
            model_.Package: Version(self),
            model_.Project: Version(self),
            model_.Application: Version(self),
        }

        self._types = types

    def _forward(self, func, index, args):
        """Forward requests to an appropriate delegate"""

        item = index.internalPointer()

        try:
            delegate = self._types[type(item)]
            func = getattr(delegate, func)
        except (AttributeError, KeyError):
            func = getattr(super(DelegateProxy, self), func)

        return func(*args)

    def createEditor(self, parent, option, index):
        return self._forward(
            "createEditor", index, args=[parent, option, index])

    def setEditorData(self, editor, index):
        return self._forward("setEditorData", index, args=[editor, index])

    def setModelData(self, editor, model, index):
        return self._forward(
            "setModelData", index, args=[editor, model, index])

    def sizeHint(self, option, index):
        return self._forward("sizeHint", index, args=[option, index])

    def updateEditorGeometry(self, editor, option, index):
        return self._forward(
            "updateEditorGeometry", index, args=[editor, option, index])


class Package(QtWidgets.QStyledItemDelegate):
    def __init__(self, ctrl, parent=None):
        super(Package, self).__init__(parent)
        self._ctrl = ctrl

    def createEditor(self, parent, option, index):
        if index.column() != 1:
            return

        editor = QtWidgets.QComboBox(parent)

        return editor

    def setEditorData(self, editor, index):
        model = index.model()
        options = model.data(index, "versions")
        default = index.data(QtCore.Qt.DisplayRole)

        editor.addItems(options)
        editor.setCurrentIndex(options.index(default))

    def setModelData(self, editor, model, index):
        model = index.model()
        package = model.data(index, "name")
        options = model.data(index, "versions")
        default = model.data(index, "default")
        version = options[editor.currentIndex()]

        if not version or version == default:
            return

        self._ctrl.patch("%s==%s" % (package, version))
