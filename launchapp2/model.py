"""Data repository and wrangler

Data Flow:
  ______    _________   _____
 |      |  |         | |     |
 | Disk |  | Network | | Rez |
 |______|  |_________| |_____|
    |___       |        __|
   _____|______|_______|____
  |                         |
  |       model.py          |
  |_________________________|
                  |___
  _________       ____|__________
 |         |     |               |
 | view.py |-----| controller.py |
 |_________|     |_______________|

It is the only module with access to disk and network - either directly or
indirectly - and can be used independently from both model and view, like an
API to launchapp2. This also means that the view may access the controller,
but not vice versa as that would implicate a view when using it standalone.

### Architecture

1. Projects are `os.listdir` from disk
2. A project is chosen by the user, e.g. ATC
3. The "ATC" Rez package is discovered and queried for "apps"
4. Each "app" is resolved alongside the current project,
    providing dependencies, environment, label, icon and
    ultimately a context within which to launch a given
    application.

"""

import os
import logging
import itertools

import rez.packages_
import rez.package_filter
import rez.resolved_context
from rez.config import config

from .vendor.Qt import QtCore, QtGui, QtCompat
from .vendor import qjsonmodel, six

log = logging.getLogger(__name__)
_basestring = six.string_types[0]  # For Python 2/3
_usercount = itertools.count(1)
Finish = None

DisplayRole = QtCore.Qt.DisplayRole
IconRole = QtCore.Qt.DecorationRole


class AbstractTableModel(QtCore.QAbstractTableModel):
    ColumnToKey = {}
    Headers = []

    def __init__(self, parent=None):
        super(AbstractTableModel, self).__init__(parent)
        self.items = []

    def reset(self, items=None):
        pass

    def find(self, name):
        return next(i for i in self.items if i["name"] == name)

    def findIndex(self, name):
        return self.createIndex(
            self.items.index(self.find(name)), 0, QtCore.QModelIndex()
        )

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0

        return len(self.items)

    def columnCount(self, parent):
        return len(self.ColumnToKey)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Vertical:
            return

        if role == QtCore.Qt.DisplayRole:
            return self.Headers[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        try:
            data = self.items[row]
        except IndexError:
            return None

        try:
            value = data[role]

            if isinstance(value, list):
                # Prevent edits
                value = value[:]

            return value

        except KeyError:
            try:
                key = self.ColumnToKey[col][role]
            except KeyError:
                return None

        return data[key]

    def setData(self, index, value, role):
        row = index.row()
        col = index.column()

        try:
            data = self.items[row]
        except IndexError:
            return False

        try:
            data[role] = value
        except KeyError:
            key = self.ColumnToKey[col][role]
            data[key] = value

        QtCompat.dataChanged(self, index, index, [role])

        return True


class ApplicationModel(AbstractTableModel):
    ColumnToKey = {
        0: {
            QtCore.Qt.DisplayRole: "label",
            QtCore.Qt.DecorationRole: "icon",
        },
        1: {
            QtCore.Qt.DisplayRole: "version",
        }
    }

    Headers = [
        "application",
        "version"
    ]

    def reset(self, applications=None):
        applications = applications or []

        self.beginResetModel()
        self.items[:] = []

        for app in applications:
            root = os.path.dirname(app.uri)

            data = getattr(app, "_data", {})
            icons = data.get("icons")
            icons = icons or getattr(app, "_icons", {})  # backwards comp
            label = data.get("label", app.name)
            tools = getattr(app, "tools", None) or [app.name]

            item = {
                "name": app.name,
                "label": label,
                "version": str(app.version),
                "icon": QtGui.QIcon(
                    icons.get("32x32", "").format(root=root)
                ),
                "package": app,
                "context": None,
                "active": True,
                "hidden": data.get("hidden", False),

                # Whether or not to open a separate console for this app
                "detached": False,

                # Current tool
                "tool": None,

                # All available tools
                "tools": tools,
            }

            self.items.append(item)

        self.endResetModel()

    def data(self, index, role):
        row = index.row()

        try:
            data = self.items[row]
        except IndexError:
            return None

        if data["hidden"]:
            if role == QtCore.Qt.ForegroundRole:
                return QtGui.QColor("gray")

        return super(ApplicationModel, self).data(index, role)


def is_local(pkg):
    if pkg.resource.repository_type != "filesystem":
        return False

    local_path = config.local_packages_path
    local_path = os.path.abspath(local_path)
    local_path = os.path.normpath(local_path)

    pkg_path = pkg.resource.location
    pkg_path = os.path.abspath(pkg_path)
    pkg_path = os.path.normpath(pkg_path)

    return pkg_path.startswith(local_path)


class PackagesModel(AbstractTableModel):
    ColumnToKey = {
        0: {
            QtCore.Qt.DisplayRole: "label",
            QtCore.Qt.DecorationRole: "icon",
        },
        1: {
            QtCore.Qt.DisplayRole: "version",
        },
        2: {
            QtCore.Qt.DisplayRole: "local",
        }
    }

    Headers = [
        "package",
        "version",
        "local",
    ]

    def __init__(self, parent=None):
        super(PackagesModel, self).__init__(parent)

        self._overrides = {}
        self._disabled = {}

    def reset(self, packages=None):
        packages = packages or []

        self.beginResetModel()
        self.items[:] = []

        for pkg in packages:
            root = os.path.dirname(pkg.uri)
            data = getattr(pkg, "_data", {})
            icons = data.get("icons")
            icons = icons or getattr(pkg, "_icons", {})  # backwards comp
            local = "(local)" if is_local(pkg) else ""
            label = data.get("label", pkg.name)

            item = {
                "name": pkg.name,
                "label": label,
                "version": str(pkg.version),
                "default": str(pkg.version),
                "icon": QtGui.QIcon(
                    icons.get("32x32", "").format(root=root)
                ),
                "package": pkg,
                "override": self._overrides.get(pkg.name),
                "disabled": self._disabled.get(pkg.name, False),
                "context": None,
                "active": True,
                "versions": None,
                "local": local,
            }

            self.items.append(item)

        self.endResetModel()

    def data(self, index, role):
        row = index.row()
        col = index.column()

        try:
            data = self.items[row]
        except IndexError:
            return None

        if data["override"]:
            if role == QtCore.Qt.DisplayRole and col == 1:
                return data["override"]

            if role == QtCore.Qt.FontRole:
                font = QtGui.QFont()
                font.setBold(True)
                return font

            if role == QtCore.Qt.ForegroundRole:
                return QtGui.QColor("darkorange")

        if data["disabled"]:
            if role == QtCore.Qt.FontRole:
                font = QtGui.QFont()
                font.setBold(True)
                font.setStrikeOut(True)
                return font

            if role == QtCore.Qt.ForegroundRole:
                return QtGui.QColor("darkorange")

        try:
            if role == "versions" and data["versions"] is None:
                versions = list(rez.packages_.iter_packages(data["name"]))
                data["versions"] = sorted([str(v.version) for v in versions])

            return data[role]

        except KeyError:
            try:
                key = self.ColumnToKey[col][role]
            except KeyError:
                return None

        return data[key]

    def setData(self, index, value, role):
        if role == "override":
            default = self.data(index, "default")
            package = self.data(index, "package").name

            if value and value != default:
                log.info("Storing permanent override %s-%s" % (package, value))
                self._overrides[package] = value
            else:
                log.info("Resetting to default")
                self._overrides.pop(package, None)
                value = None

        if role == "disabled":
            package = self.data(index, "package").name
            value = bool(value)

            if value:
                log.info("Disabling %s" % package)
            else:
                log.info("Enabling %s" % package)

            self._disabled[package] = value

        return super(PackagesModel, self).setData(index, value, role)

    def flags(self, index):
        if index.column() == 1:
            return (
                QtCore.Qt.ItemIsEnabled |
                QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsEditable
            )

        return super(PackagesModel, self).flags(index)


class CommandsModel(AbstractTableModel):
    ColumnToKey = {
        0: {
            QtCore.Qt.DisplayRole: "cmd",
            QtCore.Qt.DecorationRole: "icon",
            QtCore.Qt.UserRole + 1: "niceCmd",
        },
        1: {
            QtCore.Qt.DisplayRole: "running",
        }
    }

    Headers = [
        "command",
        "status"
    ]

    def append(self, command):
        index = len(self.items)
        app = command.app
        root = os.path.dirname(app.uri)
        icons = getattr(app, "_icons", {})

        self.beginInsertRows(QtCore.QModelIndex(), index, index + 1)
        self.items.append({
            "cmd": command.cmd,
            "niceCmd": command.nicecmd,
            "pid": None,
            "running": "waiting..",
            "icon": QtGui.QIcon(
                icons.get("32x32", "").format(root=root)
            ),
            "object": command,
            "appName": app.name,
        })
        self.endInsertRows()

    def poll(self):
        self.layoutAboutToBeChanged.emit()

        for row in range(self.rowCount()):
            command = self.items[row]["object"]
            value = "running" if command.is_running() else "killed"
            index = self.createIndex(row, 0, QtCore.QModelIndex())
            self.setData(index, value, "running")

        self.layoutChanged.emit()


class JsonModel(qjsonmodel.QJsonModel):
    pass


class EnvironmentModel(JsonModel):
    def load(self, data):

        # Convert PATH environment variables to lists
        # for improved viewing experience
        for key, value in data.copy().items():
            if os.pathsep in value:
                value = value.split(os.pathsep)
            data[key] = value

        super(EnvironmentModel, self).load(data)


class TriStateSortFilterProxyModel(QtCore.QSortFilterProxyModel):
    askOrder = QtCore.Signal(int, QtCore.Qt.SortOrder)  # column, order

    def sort(self, column, order):
        return self.askOrder.emit(column, order)

    def doSort(self, column, order):
        return super(TriStateSortFilterProxyModel, self).sort(column, order)


class ProxyModel(TriStateSortFilterProxyModel):
    """A QSortFilterProxyModel with custom exclude and include rules"""

    def __init__(self, source, excludes=None, includes=None, parent=None):
        super(ProxyModel, self).__init__(parent)
        self.setSourceModel(source)

        self.excludes = excludes or dict()
        self.includes = includes or dict()

        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def data(self, index, role):
        """Handle our custom model management"""
        sindex = self.mapToSource(index)
        smodel = self.sourceModel()
        return smodel.data(sindex, role)

    def setData(self, index, value, role):
        sindex = self.mapToSource(index)
        smodel = self.sourceModel()
        return smodel.setData(sindex, value, role)

    def setup(self, include=None, exclude=None):
        include = include or []
        exclude = exclude or []

        self.excludes.clear()
        self.includes.clear()

        def _add_rule(group, role, value):
            if role not in group:
                group[role] = list()

            group[role].append(value)

        for rule in include:
            _add_rule(self.includes, *rule)

        for rule in exclude:
            _add_rule(self.excludes, *rule)

        self.invalidate()

    # Overridden methods

    def filterAcceptsRow(self, source_row, source_parent):
        """Exclude items in `self.excludes`"""
        model = self.sourceModel()

        try:
            item = model.items[source_row]
        except IndexError:
            return False

        key = getattr(item, "filter", None)
        if key is not None:
            regex = self.filterRegExp()
            if regex.pattern():
                match = regex.indexIn(key)
                return False if match == -1 else True

        for role, values in self.includes.items():
            if item.get(role) not in values:
                return False

        for role, values in self.excludes.items():
            if item.get(role) in values:
                return False

        return super(ProxyModel, self).filterAcceptsRow(
            source_row, source_parent)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return super(ProxyModel, self).rowCount(parent)
