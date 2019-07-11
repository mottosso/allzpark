import os
import time
import logging
from itertools import chain

from .vendor.Qt import QtWidgets, QtCore, QtGui, QtCompat
from .vendor import qargparse

from . import resources as res, model, delegates, util

px = res.px


class AbstractDockWidget(QtWidgets.QDockWidget):
    """Default HTML <b>docs</b>"""

    icon = ""
    advanced = False

    message = QtCore.Signal(str)  # Handled by main window

    def __init__(self, title, parent=None):
        super(AbstractDockWidget, self).__init__(title, parent)
        self.layout().setContentsMargins(15, 15, 15, 15)

        panels = {
            "help": QtWidgets.QLabel(),
            "body": QtWidgets.QStackedWidget(),
        }

        for name, widget in panels.items():
            widget.setObjectName(name)

        central = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(px(5))
        layout.addWidget(panels["help"])
        layout.addWidget(panels["body"])

        if self.__doc__:
            panels["help"].setText(self.__doc__.splitlines()[0])
        else:
            panels["help"].hide()

        self.__panels = panels

        QtWidgets.QDockWidget.setWidget(self, central)

    def setWidget(self, widget):
        body = self.__panels["body"]

        while body.widget(0):
            body.removeWidget(body.widget(0))

        body.addWidget(widget)


class App(AbstractDockWidget):
    icon = "Alert_Info_32"

    def __init__(self, ctrl, parent=None):
        super(App, self).__init__("App", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("App")

        panels = {
            "central": QtWidgets.QWidget(),
            "shortcuts": QtWidgets.QWidget(),
            "footer": QtWidgets.QWidget(),
        }

        widgets = {
            "icon": QtWidgets.QLabel(),
            "label": QtWidgets.QLabel("Autodesk Maya"),
            "version": QtWidgets.QComboBox(),
            "tool": QtWidgets.QToolButton(),

            "commands": SlimTableView(),
            "extras": SlimTableView(),
            "lastUsed": QtWidgets.QLabel(),

            "args": qargparse.QArgumentParser([
                qargparse.Choice("tool", help=(
                    "Which executable within the context of this application"
                )),
                qargparse.Boolean("detached", help=(
                    "Spawn a dedicated console for this executable\n"
                    "Typically only necessary for console applications. "
                    "If you find that an executable doesn't provide a window, "
                    "such as mayapy, then you probably want detached."
                )),
            ]),

            # Shortcuts
            "environment": QtWidgets.QToolButton(),
            "packages": QtWidgets.QToolButton(),
            "terminal": QtWidgets.QToolButton(),

            "launchBtn": QtWidgets.QPushButton("Launch"),
        }

        # Expose to CSS
        for name, widget in chain(panels.items(), widgets.items()):
            widget.setAttribute(QtCore.Qt.WA_StyledBackground)
            widget.setObjectName(name)

        layout = QtWidgets.QHBoxLayout(panels["shortcuts"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(widgets["environment"])
        layout.addWidget(widgets["packages"])
        layout.addWidget(widgets["terminal"])
        layout.addWidget(QtWidgets.QWidget(), 1)  # push to the left

        layout = QtWidgets.QHBoxLayout(panels["footer"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["launchBtn"])

        layout = QtWidgets.QGridLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(px(10))
        layout.setVerticalSpacing(0)

        def Spacer():
            return QtWidgets.QLabel("")

        layout.addWidget(widgets["icon"], 0, 0, 2, 1)
        layout.addWidget(widgets["label"], 0, 1, QtCore.Qt.AlignTop)
        layout.addWidget(widgets["lastUsed"], 1, 1, QtCore.Qt.AlignTop)
        layout.addWidget(widgets["args"], 5, 0, 1, 2)
        layout.addWidget(widgets["commands"], 6, 0, 1, 2)
        layout.addWidget(QtWidgets.QWidget(), 15, 0)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(15, 1)
        layout.addWidget(panels["footer"], 40, 0, 1, 2)

        widgets["icon"].setPixmap(res.pixmap("Alert_Info_32"))
        widgets["environment"].setIcon(res.icon(Environment.icon))
        widgets["packages"].setIcon(res.icon(Packages.icon))
        widgets["terminal"].setIcon(res.icon(Console.icon))
        widgets["tool"].setText("maya")

        widgets["args"].changed.connect(self.on_arg_changed)

        widgets["launchBtn"].setCheckable(True)
        widgets["launchBtn"].clicked.connect(self.on_launch_clicked)

        proxy_model = model.ProxyModel(ctrl.models["commands"])
        widgets["commands"].setModel(proxy_model)

        self._ctrl = ctrl
        self._panels = panels
        self._widgets = widgets
        self._proxy = proxy_model

        self.setWidget(panels["central"])

    def on_launch_clicked(self):
        self._ctrl.launch()

    def on_arg_changed(self, arg):
        if arg["name"] not in ("detached", "tool"):
            return

        ctrl = self._ctrl
        model = ctrl.models["apps"]
        app_name = ctrl.state["appName"]
        app_index = model.findIndex(app_name)
        value = arg.read()
        model.setData(app_index, value, arg["name"])

    def refresh(self, index):
        name = index.data(QtCore.Qt.DisplayRole)
        icon = index.data(QtCore.Qt.DecorationRole)

        if icon:
            icon = icon.pixmap(QtCore.QSize(px(32), px(32)))
            self._widgets["icon"].setPixmap(icon)

        self._widgets["label"].setText(name)

        last_used = self._ctrl.state.retrieve("app/%s/lastUsed" % name)
        last_used = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(float(last_used))
        ) if last_used else "Never"
        last_used = "Last used: %s" % last_used

        self._widgets["lastUsed"].setText("%s" % last_used)

        model = index.model()
        tools = model.data(index, "tools")
        default_tool = model.data(index, "tool") or tools[0]
        arg = self._widgets["args"].find("tool")
        arg.reset(tools[:], default_tool)

        self._proxy.setup(include=[
            ("appName", name),
            ("running", "running"),
        ])


class Console(AbstractDockWidget):
    """Debugging information, mostly for developers"""

    icon = "Prefs_Screen_32"

    def __init__(self, parent=None):
        super(Console, self).__init__("Console", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Console")

        panels = {
            "central": QtWidgets.QWidget()
        }

        widgets = {
            "text": QtWidgets.QTextEdit()
        }

        self.setWidget(panels["central"])

        widgets["text"].setReadOnly(True)

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["text"])

        self._widgets = widgets

    def append(self, line, level=logging.INFO):
        color = {
            logging.WARNING: "<font color=\"red\">",
        }.get(level, "<font color=\"#222\">")

        line = "%s%s</font><br>" % (color, line)

        cursor = self._widgets["text"].textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        self._widgets["text"].setTextCursor(cursor)
        self._widgets["text"].insertHtml(line)

        scrollbar = self._widgets["text"].verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


class Packages(AbstractDockWidget):
    """Packages associated with the currently selected application"""

    icon = "File_Archive_32"
    advanced = True

    def __init__(self, ctrl, parent=None):
        super(Packages, self).__init__("Packages", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Packages")

        panels = {
            "central": QtWidgets.QWidget()
        }

        widgets = {
            "view": SlimTableView(),
            "status": QtWidgets.QStatusBar(),
        }

        self.setWidget(panels["central"])

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(widgets["view"])
        layout.addWidget(widgets["status"])

        widgets["view"].setStretch(2)
        widgets["view"].setItemDelegate(delegates.Package(ctrl, self))
        widgets["view"].setEditTriggers(widgets["view"].DoubleClicked)
        widgets["view"].verticalHeader().setDefaultSectionSize(px(20))
        widgets["view"].customContextMenuRequested.connect(self.on_right_click)

        widgets["status"].setSizeGripEnabled(False)

        self._ctrl = ctrl
        self._widgets = widgets

    def set_model(self, model_):
        proxy_model = model.ProxyModel(model_)
        self._widgets["view"].setModel(proxy_model)

        model_.modelReset.connect(self.on_model_changed)
        model_.dataChanged.connect(self.on_model_changed)

    def on_model_changed(self):
        model = self._widgets["view"].model()
        model = model.sourceModel()

        package_count = model.rowCount()
        override_count = len([i for i in model.items if i["override"]])
        disabled_count = len([i for i in model.items if i["disabled"]])

        self._widgets["status"].showMessage(
            "%d Packages, %d Overridden, %d Disabled" % (
                package_count,
                override_count,
                disabled_count,
            ))

    def on_right_click(self, position):
        view = self._widgets["view"]
        index = view.indexAt(position)

        if not index.isValid():
            # Clicked outside any item
            return

        model = index.model()
        menu = QtWidgets.QMenu(self)
        edit = QtWidgets.QAction("Edit", menu)
        disable = QtWidgets.QAction("Disable", menu)
        default = QtWidgets.QAction("Set to default", menu)
        earliest = QtWidgets.QAction("Set to earliest", menu)
        latest = QtWidgets.QAction("Set to latest", menu)
        openfile = QtWidgets.QAction("Open file location", menu)
        copyfile = QtWidgets.QAction("Copy file location", menu)

        disable.setCheckable(True)
        disable.setChecked(model.data(index, "disabled"))

        menu.addAction(edit)
        menu.addAction(disable)
        menu.addSeparator()
        menu.addAction(default)
        menu.addAction(earliest)
        menu.addAction(latest)
        menu.addSeparator()
        menu.addAction(openfile)
        menu.addAction(copyfile)
        menu.move(QtGui.QCursor.pos())

        picked = menu.exec_()

        if picked is None:
            return  # Cancelled

        if picked == edit:
            self._widgets["view"].edit(index)

        if picked == default:
            model.setData(index, None, "override")
            model.setData(index, False, "disabled")
            self.message.emit("Package set to default")

        if picked == earliest:
            versions = model.data(index, "versions")
            model.setData(index, versions[0], "override")
            model.setData(index, False, "disabled")
            self.message.emit("Package set to earliest")

        if picked == latest:
            versions = model.data(index, "versions")
            model.setData(index, versions[-1], "override")
            model.setData(index, False, "disabled")
            self.message.emit("Package set to latest version")

        if picked == openfile:
            package = model.data(index, "package")
            fname = os.path.join(package.root, "package.py")
            util.open_file_location(fname)
            self.message.emit("Opened %s" % fname)

        if picked == copyfile:
            package = model.data(index, "package")
            fname = os.path.join(package.root, "package.py")
            clipboard = QtWidgets.QApplication.instance().clipboard()
            clipboard.setText(fname)
            self.message.emit("Copied %s" % fname)

        if picked == disable:
            model.setData(index, None, "override")
            model.setData(index, disable.isChecked(), "disabled")
            self.message.emit("Package disabled")


class Context(AbstractDockWidget):
    """Full context relative the currently selected application"""

    icon = "App_Generic_4_32"
    advanced = True

    def __init__(self, parent=None):
        super(Context, self).__init__("Context", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Context")

        panels = {
            "central": QtWidgets.QWidget()
        }

        widgets = {
            "view": QtWidgets.QTreeView()
        }

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["view"])

        self._panels = panels
        self._widgets = widgets

        widgets["view"].setSortingEnabled(True)
        self.setWidget(panels["central"])

    def set_model(self, model_):
        proxy_model = QtCore.QSortFilterProxyModel()
        proxy_model.setSourceModel(model_)
        self._widgets["view"].setModel(proxy_model)


class Environment(AbstractDockWidget):
    """Full environment relative the currently selected application"""

    icon = "App_Heidi_32"
    advanced = True

    def __init__(self, parent=None):
        super(Environment, self).__init__("Environment", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Environment")

        panels = {
            "central": QtWidgets.QWidget()
        }

        widgets = {
            "view": QtWidgets.QTreeView()
        }

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["view"])

        self._panels = panels
        self._widgets = widgets

        widgets["view"].setSortingEnabled(True)
        self.setWidget(panels["central"])

    def set_model(self, model_):
        proxy_model = QtCore.QSortFilterProxyModel()
        proxy_model.setSourceModel(model_)
        self._widgets["view"].setModel(proxy_model)


class Commands(AbstractDockWidget):
    """Currently running commands"""

    icon = "App_Pulse_32"
    advanced = True

    def __init__(self, parent=None):
        super(Commands, self).__init__("Commands", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Commands")

        panels = {
            "central": QtWidgets.QWidget(),
            "body": QtWidgets.QWidget(),
            "footer": QtWidgets.QWidget(),
        }

        widgets = {
            "view": SlimTableView(),
            "command": QtWidgets.QLineEdit(),
            "stdout": QtWidgets.QListView(),
            "stderr": QtWidgets.QListView(),
        }

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(panels["body"])
        layout.addWidget(panels["footer"])

        layout = QtWidgets.QVBoxLayout(panels["body"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["view"])

        layout = QtWidgets.QVBoxLayout(panels["footer"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["command"])
        # layout.addWidget(widgets["stderr"])
        # layout.addWidget(widgets["stderr"])

        widgets["view"].setSortingEnabled(True)
        widgets["view"].customContextMenuRequested.connect(self.on_right_click)
        widgets["command"].setReadOnly(True)

        self._panels = panels
        self._widgets = widgets

        self.setWidget(panels["central"])

    def on_selection_changed(self, selected, deselected):
        selected = selected.indexes()[0]
        model = selected.model()
        cmd = model.data(selected, "niceCmd")
        self._widgets["command"].setText(cmd)

    def set_model(self, model_):
        proxy_model = model.ProxyModel(model_)
        self._widgets["view"].setModel(proxy_model)

        smodel = self._widgets["view"].selectionModel()
        smodel.selectionChanged.connect(self.on_selection_changed)

    def on_right_click(self, position):
        view = self._widgets["view"]
        index = view.indexAt(position)

        if not index.isValid():
            # Clicked outside any item
            return

        model = index.model()

        menu = QtWidgets.QMenu(self)
        kill = QtWidgets.QAction("Kill", menu)
        copy_command = QtWidgets.QAction("Copy command", menu)
        copy_pid = QtWidgets.QAction("Copy pid", menu)

        menu.addAction(kill) if os.name != "nt" else None
        menu.addAction(copy_command)
        menu.addAction(copy_pid)
        menu.move(QtGui.QCursor.pos())

        picked = menu.exec_()

        if picked is None:
            return  # Cancelled

        if picked == kill:
            name = model.data(index, "cmd")
            if not model.data(index, "running"):
                self.message.emit("%s isn't running" % name)
                return

            self.message.emit("Killing %s" % name)
            command = model.data(index, "object")
            command.kill()

        if picked == copy_pid:
            clipboard = QtWidgets.QApplication.instance().clipboard()
            command = model.data(index, "object")
            pid = str(command.pid)
            clipboard.setText(pid)
            self.message.emit("Copying %s" % pid)

        if picked == copy_command:
            clipboard = QtWidgets.QApplication.instance().clipboard()
            cmd = model.data(index, "niceCmd")
            clipboard.setText(cmd)
            self.message.emit("Copying %s" % cmd)


class Preferences(AbstractDockWidget):
    """Preferred settings relative the current user"""

    icon = "Action_GoHome_32"

    options = [
        qargparse.Info("startupProject", help=(
            "Load this project on startup"
        )),
        qargparse.Info("startupApplication", help=(
            "Load this application on startup"
        )),

        qargparse.Separator("Theme"),

        qargparse.Info("primaryColor", default="white", help=(
            "Main color of the GUI"
        )),
        qargparse.Info("secondaryColor", default="steelblue", help=(
            "Secondary color of the GUI"
        )),

        qargparse.Button("resetLayout", help=(
            "Reset stored layout to their defaults"
        )),

        qargparse.Separator("Settings"),

        qargparse.Boolean("smallIcons", enabled=False, help=(
            "Draw small icons"
        )),
        qargparse.Boolean("allowMultipleDocks", help=(
            "Allow more than one dock to exist at a time"
        )),
        qargparse.Boolean("showAdvancedControls", help=(
            "Show developer-centric controls"
        )),
        qargparse.Boolean("showAllApps", help=(
            "List everything from ALLZPARK_APPS\n"
            "not just the ones specified for a given project."
        )),
        qargparse.Boolean("showHiddenApps", help=(
            "Show apps with _data['hidden'] = True"
        )),

        qargparse.Separator("System"),

        # Provided by controller
        qargparse.Info("pythonExe"),
        qargparse.Info("pythonVersion"),
        qargparse.Info("qtVersion"),
        qargparse.Info("qtBinding"),
        qargparse.Info("qtBindingVersion"),
        qargparse.Info("rezLocation"),
        qargparse.Info("rezVersion"),
        qargparse.Info("rezConfigFile"),
        qargparse.Info("memcachedURI"),
        qargparse.InfoList("rezPackagesPath"),
        qargparse.InfoList("rezLocalPath"),
        qargparse.InfoList("rezReleasePath"),
        qargparse.Info("settingsPath"),
    ]

    def __init__(self, window, ctrl, parent=None):
        super(Preferences, self).__init__("Preferences", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Preferences")

        panels = {
            "scrollarea": QtWidgets.QScrollArea(),
            "central": QtWidgets.QWidget(),
        }

        widgets = {
            "options": qargparse.QArgumentParser(
                self.options, storage=ctrl._storage)
        }

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["options"])

        panels["scrollarea"].setWidget(panels["central"])
        panels["scrollarea"].setWidgetResizable(True)

        widgets["options"].changed.connect(self.handler)

        self._panels = panels
        self._widgets = widgets
        self._ctrl = ctrl
        self._window = window

        self.setWidget(panels["scrollarea"])

    def handler(self, argument):
        self._window.on_setting_changed(argument)


class SlimTableView(QtWidgets.QTableView):
    doSort = QtCore.Signal(int, QtCore.Qt.SortOrder)

    def __init__(self, parent=None):
        super(SlimTableView, self).__init__(parent)
        self.setShowGrid(False)
        self.verticalHeader().hide()
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)
        self._stretch = 0
        self._previous_sort = 0

    def setStretch(self, column):
        self._stretch = column

    def refresh(self):
        header = self.horizontalHeader()
        QtCompat.setSectionResizeMode(
            header, self._stretch, QtWidgets.QHeaderView.Stretch)

    def setModel(self, model_):
        model_.rowsInserted.connect(self.refresh)
        model_.modelReset.connect(self.refresh)
        super(SlimTableView, self).setModel(model_)
        self.refresh()

        if isinstance(model_, model.ProxyModel):
            self.doSort.connect(model_.doSort)
            model_.askOrder.connect(self.setSorting)
            self.setSortingEnabled(True)

            # Start out unsorted
            header = self.horizontalHeader()
            header.setSortIndicatorShown(False)
            header.setSortIndicator(0, QtCore.Qt.DescendingOrder)
            self.doSort.emit(-1, QtCore.Qt.DescendingOrder)

    def setSorting(self, column, order):
        header = self.horizontalHeader()
        is_sorted = header.isSortIndicatorShown()
        is_previous = self._previous_sort == column
        is_ascending = header.sortIndicatorOrder() == QtCore.Qt.AscendingOrder

        if is_ascending and is_sorted and is_previous:
            header.setSortIndicator(column, QtCore.Qt.DescendingOrder)
            header.setSortIndicatorShown(False)
            column = -1
        else:
            header.setSortIndicatorShown(True)

        self._previous_sort = column
        self.doSort.emit(column, order)

    def mousePressEvent(self, event):
        """Do request a context menu, but on mouse *press*, not release"""

        # Important, call this first to have the item be selected,
        # as per default, and *then* ask for a context menu. That
        # way, the menu and selection aligns.
        try:
            return super(SlimTableView, self).mousePressEvent(event)

        finally:
            if event.button() == QtCore.Qt.RightButton:
                self.customContextMenuRequested.emit(event.pos())
