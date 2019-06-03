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

from .vendor.Qt import QtCore, QtGui, QtCompat
from .vendor import qjsonmodel, qhonestmodel, six
from . import util

log = logging.getLogger(__name__)
_basestring = six.string_types[0]  # For Python 2/3
_usercount = itertools.count(1)
Finish = None


DisplayRole = QtCore.Qt.DisplayRole
IconRole = QtCore.Qt.DecorationRole

LoadedRole = qhonestmodel.LoadedRole

DefaultRole = qhonestmodel.UserRole()
PackageRole = qhonestmodel.UserRole()
FunctionRole = qhonestmodel.UserRole()
ArgsRole = qhonestmodel.UserRole()
KwargsRole = qhonestmodel.UserRole()
PathRole = qhonestmodel.UserRole()
LabelRole = qhonestmodel.UserRole()
ContextRole = qhonestmodel.UserRole()
VersionRole = qhonestmodel.UserRole()
VersionsRole = qhonestmodel.UserRole()
OverriddenRole = qhonestmodel.UserRole()


class Main(qhonestmodel.QHonestTreeModel):
    pass


class Root(qhonestmodel.QHonestItem):
    """Hosts one or more Project items"""
    def __init__(self, path):
        super(Root, self).__init__("root")
        self[DisplayRole][1] = ""  # 2 columns
        self[PathRole][0] = path

        projects = qhonestmodel.QHonestItem("projects")
        projects[DisplayRole][1] = "Available projects on disk"
        projects.appendChild(
            qhonestmodel.QPromiseItem("...", func=self.fetch)
        )

        commands = qhonestmodel.QHonestItem("commands")
        commands[DisplayRole][1] = "Currently running commands"

        settings = qhonestmodel.QHonestItem("settings")
        settings[DisplayRole][1] = "User preferences"

        self.appendChild(projects)
        self.appendChild(commands)
        self.appendChild(settings)

    @util.cached
    def fetch(self):
        print("Fetching projects..")
        path = self[PathRole][0]

        try:
            _, dirs, files = next(os.walk(path))
        except StopIteration:
            log.error("Could not find projects in %s" % path)
            return

        for dirname in dirs:
            # Packages use _ in place of -
            rezname = dirname.replace("-", "_")
            yield Project(rezname)
        yield Finish


class Project(qhonestmodel.QHonestItem):
    def __init__(self, text):
        super(Project, self).__init__(text)
        self[DisplayRole][1] = ""
        self[DefaultRole][1] = text
        self[LoadedRole][0] = False

        versions = qhonestmodel.QPromiseItem("Loading versions...", func=self.fetch)
        self.appendChild(versions)

    def flags(self, index):
        flags = super(Project, self).flags(index)

        # Let the user edit the version of this package
        if self[LoadedRole][0] and index.column() == 1:
            flags |= QtCore.Qt.ItemIsEditable

        return flags

    def fetch(self, count=5):
        request = self[DisplayRole][0]
        it = rez.packages_.iter_packages(request)

        package = None
        for index, package in enumerate(it):
            yield ProjectVersion(package)

        if package:
            self[DisplayRole][1] = str(package.version)

        self[LoadedRole][0] = True

        yield Finish


class ProjectVersion(qhonestmodel.QHonestItem):
    def __init__(self, package):
        super(ProjectVersion, self).__init__(str(package.version))
        self[PackageRole][0] = package

        apps = qhonestmodel.QPromiseItem("Loading applications...", func=self.fetch)
        self.appendChild(apps)

    def fetch(self):
        package = self[PackageRole][0]
        apps = getattr(package, "_apps", [])

        for app in apps:
            assert isinstance(app, _basestring)
            yield Application(app)
        yield Finish


class Application(qhonestmodel.QHonestItem):
    def __init__(self, text):
        super(Application, self).__init__(text)
        self[PackageRole][0] = None
        self[IconRole][0] = None
        self[ContextRole][0] = None
        self[VersionRole][0] = None
        self[LoadedRole][0] = False

        context = qhonestmodel.QPromiseItem("Resolving context...", func=self.fetch)
        self.appendChild(context)

    def flags(self, index):
        flags = super(Application, self).flags(index)

        # Let the user edit the version of this package
        if self[LoadedRole][0] and index.column() == 1:
            flags |= QtCore.Qt.ItemIsEditable

        return flags

    def fetch(self):
        app_name = self[DisplayRole][0]
        project_version = self.parent()[DisplayRole][0]
        project_name = self.parent().parent()[DisplayRole][0]
        request = ["%s-%s" % (project_name, project_version), app_name]

        rule = rez.package_filter.Rule.parse_rule("*.beta")
        PackageFilterList = rez.package_filter.PackageFilterList
        package_filter = PackageFilterList.singleton.copy()
        package_filter.add_exclusion(rule)

        context = rez.resolved_context.ResolvedContext(
            request, package_filter=package_filter)

        if not context.success:
            description = context.failure_description
            raise rez.exceptions.ResolveError(description)

        # Convert app `name` to Rez Package
        # E.g. "maya" --> Package<'maya-2018.0.1'>
        try:
            package = next(
                package for package in context.resolved_packages
                if package.name == app_name
            )
        except StopIteration:
            raise rez.exceptions.ResolveError(
                "Couldn't find application amongst "
                "resolved packages, this is a bug."
            )

        # Append package metadata
        for role, value in _parse_package(package).items():
            self[role][0] = value

        self[ContextRole][0] = context
        self[DisplayRole][1] = str(package.version)

        environ = {}
        for key, value in context.get_environ().items():
            if os.pathsep in value:
                value = value.split(os.pathsep)
            environ[key] = value

        env = qhonestmodel.QHonestItem.from_json("environment", environ)
        ctx = qhonestmodel.QHonestItem.from_json("context", context.to_dict())

        yield env
        yield ctx

        packages = qhonestmodel.QHonestItem("packages")
        for package in context.resolved_packages:

            # Needless
            if package == self[PackageRole][0]:
                continue

            if package.name == project_name:
                continue

            packages.appendChild(Package(package))

        yield packages

        self[LoadedRole][0] = True

        yield Finish


def _parse_package(package):
    root = os.path.dirname(package.uri)
    data = getattr(package, "_data", {})
    icons = data.get("icons", {})

    # Backwards compatibility
    if not icons and hasattr(package, "_icons"):
        icons = package._icons

    return {
        PackageRole: package,
        VersionRole: str(package.version),
        DisplayRole: data.get("label", package.name),
        IconRole: QtGui.QIcon(icons.get("32x32", "").format(root=root)),
    }


class Package(qhonestmodel.QHonestItem):
    """TODO: This could be a singleton"""

    def __init__(self, package):
        super(Package, self).__init__(package.qualified_package_name)
        self[DisplayRole][1] = str(package.version)
        self[DefaultRole][1] = str(package.version)

        for role, value in _parse_package(package).items():
            self[role][0] = value

        context = qhonestmodel.QPromiseItem("Loading versions...", func=self.fetch)
        self.appendChild(context)

    def flags(self, index):
        flags = super(Package, self).flags(index)

        # Let the user edit the version of this package
        if index.column() == 1:
            flags |= QtCore.Qt.ItemIsEditable

        return flags

    def fetch(self):
        request = self[PackageRole][0].name
        it = rez.packages_.iter_packages(request)

        for index, package in enumerate(it):
            yield PackageVersion(str(package.version))
        yield Finish


class PackageVersion(qhonestmodel.QHonestItem):
    def childCount(self):
        return 0


class AbstractTableModel(QtCore.QAbstractTableModel):
    ColumnToKey = {}
    Headers = []

    def __init__(self, parent=None):
        super(AbstractTableModel, self).__init__(parent)
        self.items = []

    def reset(self, items=None):
        pass

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
            return data[role]
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
            QtCore.Qt.DisplayRole: "name",
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
            icons = getattr(app, "_icons", {})
            item = {
                "name": app.name,
                "version": str(app.version),
                "icon": QtGui.QIcon(
                    icons.get("32x32", "").format(root=root)
                ),
                "package": app,
                "context": None,
                "active": True,
                "overridden": None,
            }

            self.items.append(item)

        self.endResetModel()


class PackagesModel(AbstractTableModel):
    ColumnToKey = {
        0: {
            QtCore.Qt.DisplayRole: "name",
            QtCore.Qt.DecorationRole: "icon",
        },
        1: {
            QtCore.Qt.DisplayRole: "version",
        }
    }

    Headers = [
        "package",
        "version",
    ]

    def reset(self, packages=None):
        packages = packages or []

        self.beginResetModel()
        self.items[:] = []

        for pkg in packages:
            root = os.path.dirname(pkg.uri)
            icons = getattr(pkg, "_icons", {})
            item = {
                "name": pkg.name,
                "version": str(pkg.version),
                "override": False,
                "icon": QtGui.QIcon(
                    icons.get("32x32", "").format(root=root)
                ),
                "package": pkg,
                "context": None,
                "active": True,
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

        override = data["override"]

        if override:
            if role == QtCore.Qt.DisplayRole and col == 1:
                return data["override"]

            if role == QtCore.Qt.FontRole:
                font = QtGui.QFont()
                font.setBold(True)
                return font

            if role == QtCore.Qt.ForegroundRole:
                return QtGui.QColor("darkorange")

        try:
            return data[role]
        except KeyError:
            try:
                key = self.ColumnToKey[col][role]
            except KeyError:
                return None

        return data[key]

    def setData(self, index, value, role):
        print("Setting packages data..")
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
            "running": "waiting..",
            "icon": QtGui.QIcon(
                icons.get("32x32", "").format(root=root)
            ),
            "object": command,
            "appName": command.app.name,
        })
        self.endInsertRows()

    def poll(self):
        for row in range(self.rowCount()):
            command = self.items[row]["object"]
            value = "running" if command.is_running() else "killed"
            index = self.index(row, 1)
            self.setData(index, value, QtCore.Qt.DisplayRole)


class JsonModel(qjsonmodel.QJsonModel):
    pass


class ProxyModel(QtCore.QSortFilterProxyModel):
    """A QSortFilterProxyModel with custom exclude and include rules"""

    def __init__(self, source, excludes=None, includes=None, parent=None):
        super(ProxyModel, self).__init__(parent)
        self.setSourceModel(source)

        self.excludes = excludes or dict()
        self.includes = includes or dict()

        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

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
