from .vendor.Qt import QtWidgets, QtCore


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
