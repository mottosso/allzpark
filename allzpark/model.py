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
API to allzpark. This also means that the view may access the controller,
but not vice versa as that would implicate a view when using it standalone.

### Architecture

1. Profiles are `os.listdir` from disk
2. A profile is chosen by the user, e.g. ATC
3. The "ATC" Rez package is discovered and queried for "apps"
4. Each "app" is resolved alongside the current profile,
    providing dependencies, environment, label, icon and
    ultimately a context within which to launch a given
    application.

"""

import re
import os
import logging
import itertools

from . import allzparkconfig, util, resources as res
from . import _rezapi as rez

from .vendor.Qt import QtCore, QtGui, QtCompat
from .vendor import qjsonmodel, six

# Optional third-party dependencies
try:
    from localz import lib as localz
except ImportError:
    localz = None

log = logging.getLogger(__name__)
_basestring = six.string_types[0]  # For Python 2/3
_usercount = itertools.count(1)
Finish = None
Latest = None  # Enum
NoVersion = None

DisplayRole = QtCore.Qt.DisplayRole
IconRole = QtCore.Qt.DecorationRole
LocalizingRole = QtCore.Qt.UserRole + 1
BetaRole = QtCore.Qt.UserRole + 2
LatestRole = QtCore.Qt.UserRole + 3
NameRole = QtCore.Qt.UserRole + 4


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

        roles = [role] if isinstance(role, int) else []
        QtCompat.dataChanged(self, index, index, roles)

        return True


def parse_icon(root, template):
    try:
        fname = template.format(
            root=root,
            width=32,
            height=32,
            w=32,
            h=32
        )

    except KeyError:
        fname = ""

    return QtGui.QIcon(fname)


class ResolvedPackagesModel(AbstractTableModel):
    ColumnToKey = {
        0: {
            QtCore.Qt.DisplayRole: "label",
            QtCore.Qt.DecorationRole: "icon",
        },
        1: {
            QtCore.Qt.DisplayRole: "version",
        },
        2: {
            QtCore.Qt.DisplayRole: "state",
        },
        3: {
            QtCore.Qt.DisplayRole: "latest",
        },
        4: {
            QtCore.Qt.DisplayRole: "beta",
        },
    }

    def __init__(self, *args, **kwargs):
        super(ResolvedPackagesModel, self).__init__(*args, **kwargs)
        self._broken_icon = res.icon("Action_Stop_1_32.png")
        self._overrides = {}
        self._disabled = {}

    @property
    def overrides(self):
        return self._overrides

    @property
    def disabled(self):
        return self._disabled

    def reset(self, packages=None):
        packages = packages or dict()

        self.beginResetModel()
        self.items[:] = []

        for app_request, app_data in packages.items():
            app = app_data["app"]
            versions = app_data["versions"]

            self._add_item(app_request, app_request, app, versions)

            for pkg in app_data["packages"]:
                self._add_item(pkg.name, app_request, pkg)

        self.endResetModel()

    def _add_item(self, name, app_request, pkg, versions=None):
        root = pkg.root
        is_app = versions is not None
        data = allzparkconfig.metadata_from_package(pkg)
        tools = getattr(pkg, "tools", None) or [pkg.name]
        version = str(pkg.version)
        relocatable = localz.is_relocatable(pkg) if localz else False
        state = (
            "(dev)" if is_local(pkg) else
            "(localised)" if is_localised(pkg) else
            ""
        )

        item = {
            "_isApp": is_app,

            "name": name,
            "label": data["label"],
            "version": version,
            "versions": versions or [version],
            "icon": parse_icon(root, template=data["icon"]),
            "package": pkg,
            "context": None,
            "active": True,

            "family": pkg.name,
            "request": app_request,
            "hidden": data["hidden"],
            "broken": isinstance(pkg, BrokenPackage),

            "default": version,
            "override": self._overrides.get(pkg.name),
            "disabled": self._disabled.get(pkg.name, False),
            "state": state,
            "relocatable": relocatable,
            "localizing": False,  # in progress

            # Whether or not to open a separate console for this app
            "detached": False,
            # Current tool
            "tool": None,
            # All available tools
            "tools": tools,
        }

        self.items.append(item)

    def data(self, index, role):
        row = index.row()
        col = index.column()

        try:
            data = self.items[row]
        except IndexError:
            return None

        if data["hidden"]:
            if role == QtCore.Qt.ForegroundRole:
                return QtGui.QColor("gray")

        if data["broken"]:
            if role == QtCore.Qt.ForegroundRole:
                return QtGui.QColor("red")

            if role == QtCore.Qt.FontRole:
                font = QtGui.QFont()
                font.setBold(True)
                return font

            if role == QtCore.Qt.DisplayRole:
                if col == 0:
                    return data["label"] + " (failed)"

            if role == IconRole:
                if col == 0:
                    return self._broken_icon

        if data["override"]:
            if role == QtCore.Qt.DisplayRole and col == 1:
                return data["override"]

            if role == QtCore.Qt.FontRole:
                font = QtGui.QFont()
                font.setBold(True)
                return font

            if role == QtCore.Qt.ForegroundRole:
                return QtGui.QColor("darkorange")

        if data["disabled"] or data["localizing"]:
            if role == QtCore.Qt.FontRole:
                font = QtGui.QFont()
                font.setBold(True)
                font.setStrikeOut(True)
                return font

            if role == QtCore.Qt.ForegroundRole:
                return QtGui.QColor("darkorange")

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

        if key == "beta":
            version = data["override"] or data["version"]
            return "x" if re.findall(r".beta$", version) else ""

        if key == "latest":
            # TODO: this is not the real latest
            version = data["override"] or data["version"]
            latest = data["versions"][-1]
            return "x" if version == latest else ""

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

        return super(ResolvedPackagesModel, self).setData(index, value, role)

    def flags(self, index):
        if index.column() == 1:
            return (
                QtCore.Qt.ItemIsEnabled |
                QtCore.Qt.ItemIsSelectable |
                QtCore.Qt.ItemIsEditable
            )

        return super(ResolvedPackagesModel, self).flags(index)


class BrokenContext(object):
    broken_dict = {"error": "Failed context"}

    def __init__(self, app_name, request):
        self.resolved_packages = [BrokenPackage(app_name)]
        self.success = False
        self.timestamp = 0

        self._request = request

    def requested_packages(self):
        return self._request

    def to_dict(self, *args, **kwargs):
        return self.broken_dict

    def get_environ(self, *args, **kwargs):
        raise rez.ResolvedContextError("This is a broken context.")


class BrokenPackage(object):
    def __str__(self):
        return self.name

    def __init__(self, request):
        request = rez.PackageRequest(request)
        versions = request.range.to_versions() or [None]

        self.name = request.name
        self.version = versions[-1]
        self.qualified_name = "%s-%s" % (self.name, str(self.version))
        self.uri = ""
        self.root = ""
        self.relocatable = False
        self.requires = []
        self.resource = type(
            "BrokenResource", (object,), {"repository_type": None}
        )()

        self._data = {
            "label": request.name,
        }


def is_local(pkg):
    if pkg.resource.repository_type != "filesystem":
        return False

    local_path = rez.config.local_packages_path
    local_path = os.path.abspath(local_path)
    local_path = os.path.normpath(local_path)

    pkg_path = pkg.resource.location
    pkg_path = os.path.abspath(pkg_path)
    pkg_path = os.path.normpath(pkg_path)

    return pkg_path.startswith(local_path)


def is_localised(pkg):
    if localz:
        root = util.normpath(pkg.root)
        path = util.normpath(localz.localized_packages_path())
        return root.startswith(path)
    else:
        return False


class CommandsModel(AbstractTableModel):
    ColumnToKey = {
        0: {
            QtCore.Qt.DisplayRole: "cmd",
            QtCore.Qt.DecorationRole: "icon",
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
        data = allzparkconfig.metadata_from_package(app)

        self.beginInsertRows(QtCore.QModelIndex(), index, index + 1)
        self.items.append({
            "cmd": command.cmd,
            "pid": None,
            "running": "waiting..",
            "icon": parse_icon(root, template=data["icon"]),
            "object": command,
            "appName": app.name,
        })
        self.endInsertRows()

    def poll(self):
        self.layoutAboutToBeChanged.emit()

        running_count = 0
        for row in range(self.rowCount()):
            command = self.items[row]["object"]
            is_running = command.is_running()
            running_count += is_running
            value = "running" if is_running else "killed"
            index = self.createIndex(row, 0, QtCore.QModelIndex())
            self.setData(index, value, "running")

        self.layoutChanged.emit()

        return running_count


class JsonModel(qjsonmodel.QJsonModel):

    JsonRole = QtCore.Qt.UserRole + 1

    def setData(self, index, value, role):
        # Support copy/paste, but prevent edits
        return False

    def flags(self, index):
        flags = super(JsonModel, self).flags(index)
        return QtCore.Qt.ItemIsEditable | flags

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            if index.column() == 0:
                return item.key

            if index.column() == 1:
                return item.value

        if role == self.JsonRole:
            return self.json(item)

        return super(JsonModel, self).data(index, role)

    reset = qjsonmodel.QJsonModel.clear


class EnvironmentModel(JsonModel):
    def load(self, data):
        # Convert PATH environment variables to lists
        # for improved viewing experience
        for key, value in data.copy().items():
            if os.pathsep in value:
                value = value.split(os.pathsep)
            data[key] = value

        super(EnvironmentModel, self).load(data)


class ContextModel(JsonModel):
    pass


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


class ApplicationProxyModel(ProxyModel):

    Headers = [
        "application",
        "version"
    ]

    def columnCount(self, parent):
        return len(self.Headers)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Vertical:
            return

        if role == QtCore.Qt.DisplayRole:
            return self.Headers[section]


class PackagesProxyModel(ProxyModel):

    Headers = [
        "package",
        "version",
        "state",
        "latest",
        "beta",
    ]

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Vertical:
            return

        if role == QtCore.Qt.DisplayRole:
            return self.Headers[section]


class TreeItem(dict):

    def __init__(self, data=None):
        super(TreeItem, self).__init__(data or {})
        self._children = list()
        self._parent = None

    def walk(self):
        for i in self._children:
            yield i
        for i in self._children:
            for j in i.walk():
                yield j

    def row(self):
        if self._parent is not None:
            siblings = self.parent().children()
            return siblings.index(self)

    def parent(self):
        return self._parent

    def child(self, row):
        if row >= len(self._children):
            log.warning("Invalid row as child: {0}".format(row))
            return
        return self._children[row]

    def children(self):
        return self._children

    def childCount(self):
        return len(self._children)

    def add_child(self, child):
        child._parent = self
        self._children.append(child)


class AbstractTreeModel(QtCore.QAbstractItemModel):
    ColumnToKey = {}
    Headers = []

    def __init__(self, parent=None):
        super(AbstractTreeModel, self).__init__(parent)
        self.root = TreeItem()

    def reset(self, items=None):
        pass

    def find(self, name):
        walk = self.root.walk()
        return next((i for i in walk if i.get("name") == name), None)

    def findIndex(self, name):
        item = self.find(name)
        if item is None:
            return QtCore.QModelIndex()
        else:
            return self.createIndex(item.row(), 0, item)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            item = parent.internalPointer()
        else:
            item = self.root

        return item.childCount()

    def columnCount(self, parent):
        return len(self.ColumnToKey)

    def index(self, row, column, parent):
        if not parent.isValid():
            parent_item = self.root
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Vertical:
            return

        if role == QtCore.Qt.DisplayRole:
            return self.Headers[section]

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()
        col = index.column()

        try:
            value = item[role]

            if isinstance(value, list):
                # Prevent edits
                value = value[:]

            return value

        except KeyError:
            try:
                key = self.ColumnToKey[col][role]
            except KeyError:
                return None

        return item[key]

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid():
            item = index.internalPointer()
            col = index.column()

            try:
                item[role] = value
            except KeyError:
                key = self.ColumnToKey[col][role]
                item[key] = value

            roles = [role] if isinstance(role, int) else []
            QtCompat.dataChanged(self, index, index, roles)

            return True

        return False

    def parent(self, index):
        item = index.internalPointer()
        parent_item = item.parent()

        # If it has no parents we return invalid
        if parent_item == self.root or not parent_item:
            return QtCore.QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def add_child(self, item, parent=None):
        if parent is None:
            parent = self.root

        parent.add_child(item)


def is_filtering_recursible():
    """Does Qt binding support recursive filtering for QSortFilterProxyModel?

    Recursive filtering was introduced in Qt 5.10.

    """
    return hasattr(QtCore.QSortFilterProxyModel,
                   "setRecursiveFilteringEnabled")


class RecursiveSortFilterProxyModel(QtCore.QSortFilterProxyModel):
    """Filters to the regex if any of the children matches allow parent"""

    if is_filtering_recursible():
        def filter_accepts_parent(self, index, node):
            # With the help of `RecursiveFiltering` feature from Qt 5.10+,
            # parent always not be accepted by default.
            return False
    else:
        def filter_accepts_parent(self, index, model):
            for child_row in range(model.rowCount(index)):
                if self.filterAcceptsRow(child_row, index):
                    return True
            return False

        # Patch future function
        def setRecursiveFilteringEnabled(self, *args):
            pass

    def __init__(self, *args, **kwargs):
        super(RecursiveSortFilterProxyModel, self).__init__(*args, **kwargs)
        self.setRecursiveFilteringEnabled(True)

    def filterAcceptsRow(self, row, parent):
        model = self.sourceModel()
        source_index = model.index(row, self.filterKeyColumn(), parent)
        if source_index.isValid():
            item = source_index.internalPointer()
            if item.childCount():
                return self.filter_accepts_parent(source_index, model)

        return super(RecursiveSortFilterProxyModel,
                     self).filterAcceptsRow(row, parent)


class ProfileModel(AbstractTreeModel):
    """
    * profile category
    * profile name (label)
    * favorite
    * profile data
    """
    ColumnToKey = {
        0: {
            NameRole: "name",
            QtCore.Qt.DisplayRole: "label",
            QtCore.Qt.DecorationRole: "icon",
        },
    }

    Headers = [
        "label",
    ]

    DefaultCategory = "profiles"

    def __init__(self, parent=None):
        super(ProfileModel, self).__init__(parent)
        self.is_filtering = True
        self.current = ""
        self.favorites = set([])

        self.icons = [
            # normal
            res.icon("profile_normal"),
            # favorite
            res.icon("profile_normal_star"),
            # current
            res.icon("profile_current"),
            # current + favorite
            res.icon("profile_current_star"),
        ]

    def set_favorites(self, ctrl):
        favorites = ctrl.state.retrieve("favoriteProfiles", "").split(",")
        self.favorites = set(favorites)

    def set_current(self, name):
        previous = self.current
        self.current = name
        self.update_profile_icon(self.findIndex(previous))
        self.update_profile_icon(self.findIndex(name))

    def update_favorite(self, ctrl, index):
        if not index.isValid():
            return

        name = index.data(NameRole)

        if name in self.favorites:
            self.favorites.remove(name)
        else:
            self.favorites.add(name)

        ctrl.state.store("favoriteProfiles", ",".join(self.favorites))

    def update_profile_icon(self, index):
        if not index.isValid():
            return

        icon = self.profile_icon(index.data(NameRole))
        self.setData(index, icon, role=QtCore.Qt.DecorationRole)

    def reset(self, profiles=None):
        profiles = profiles or dict()

        self.beginResetModel()
        self.root = TreeItem()

        categories = dict()

        for name, versions in profiles.items():
            # NOTE: This model only takes the latest profile
            package = versions[Latest]
            data = allzparkconfig.metadata_from_package(package)

            item = TreeItem({
                "name": name,
                "label": data.get("label", name),
                "icon": self.profile_icon(name),
                "category": data.get("category", self.DefaultCategory),
            })

            category_name = item["category"]
            if category_name in categories:
                category = categories[category_name]
            else:
                category = TreeItem({
                    "name": None,
                    "label": category_name,
                    "icon": None,
                })
                categories[category_name] = category
                self.root.add_child(category)

            category.add_child(item)

        self.endResetModel()

    def profile_icon(self, name):
        is_favorite = (name in self.favorites) * 1
        is_current = (name == self.current) * 2
        return self.icons[is_current + is_favorite]


class ProfileProxyModel(RecursiveSortFilterProxyModel):

    def filterAcceptsRow(self, row, parent):
        model = self.sourceModel()
        regex = self.filterRegExp()
        source_index = model.index(row, self.filterKeyColumn(), parent)
        if source_index.isValid():
            item = source_index.internalPointer()

            if item.childCount():
                return self.filter_accepts_parent(source_index, model)

            elif model.is_filtering and regex.isEmpty():
                name = item["name"]
                return name == model.current or name in model.favorites

        return super(RecursiveSortFilterProxyModel,
                     self).filterAcceptsRow(row, parent)
