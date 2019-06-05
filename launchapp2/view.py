"""The view may access a controller, but not vice versa"""

import logging
from itertools import chain
from collections import OrderedDict as odict

from .vendor.Qt import QtWidgets, QtCore, QtCompat, QtGui
from .vendor import six, qargparse
from .version import version
from . import resources as res, model, delegates

px = res.px


class Window(QtWidgets.QMainWindow):
    title = "Launch App 2.0"

    def __init__(self, ctrl, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle(self.title)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setWindowIcon(QtGui.QIcon(res.find("Logo_64.png")))

        self._count = 0

        pages = odict((
            ("home", QtWidgets.QWidget()),

            # Pages matching a particular state
            ("booting", QtWidgets.QWidget()),
            ("errored", QtWidgets.QWidget()),
            ("noapps", QtWidgets.QWidget()),
        ))

        panels = {
            "pages": QtWidgets.QStackedWidget(),
            "header": QtWidgets.QWidget(),
            "body": QtWidgets.QWidget(),
            "footer": QtWidgets.QWidget(),
        }

        widgets = {
            "bootMessage": QtWidgets.QLabel("Loading.."),
            "errorMessage": QtWidgets.QLabel("Uh oh..<br>"
                                             "See Console for details"),
            "noappsMessage": QtWidgets.QLabel("No applications found"),
            "pkgnotfoundMessage": QtWidgets.QLabel(
                "One or more packages could not be found"
            ),

            # Header
            "logo": QtWidgets.QLabel(),
            "appVersion": QtWidgets.QLabel(version),

            "projectBtn": QtWidgets.QToolButton(),
            "projectMenu": QtWidgets.QMenu(),
            "projectName": QtWidgets.QLabel("None"),
            "projectVersions": QtWidgets.QComboBox(),

            "apps": SlimTableView(),

            # Error page
            "continue": QtWidgets.QPushButton("Continue"),
            "reset": QtWidgets.QPushButton("Reset"),

            "dockToggles": QtWidgets.QWidget(),

            "extraContainer": QtWidgets.QWidget(),
            "extraRequirementsRender": QtWidgets.QPushButton(),
            "extraRequirementsPrefix": QtWidgets.QLabel("rez env "),
            "extraRequirements": QtWidgets.QLineEdit(),
            "extraRequirementsSuffix": QtWidgets.QLabel(" -- maya"),

            "stateIndicator": QtWidgets.QLabel(),
        }

        # The order is reflected in the UI
        docks = odict((
            ("app", App(ctrl)),
            ("packages", Packages(ctrl)),
            ("context", Context()),
            ("environment", Environment()),
            ("console", Console()),
            ("commands", Commands()),
            ("preferences", Preferences(self, ctrl)),
        ))

        actions = {
            "projectsGroup": QtWidgets.QActionGroup(self),
            "launchToolsGroup": QtWidgets.QActionGroup(self),
            "extraRequirements": QtWidgets.QAction("Extra requirements", self)
        }

        # Expose to CSS
        for name, widget in chain(panels.items(),
                                  widgets.items(),
                                  pages.items()):
            widget.setAttribute(QtCore.Qt.WA_StyledBackground)
            widget.setObjectName(name)

        self.setCentralWidget(panels["pages"])

        # Add header to top-most portion of GUI above movable docks
        toolbar = self.addToolBar("header")
        toolbar.setObjectName("Header")
        toolbar.addWidget(panels["header"])
        toolbar.setMovable(False)

        # Fill horizontal space
        panels["header"].setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Preferred)

        for page in pages.values():
            panels["pages"].addWidget(page)

        # Layout
        layout = QtWidgets.QVBoxLayout(pages["booting"])
        layout.addWidget(QtWidgets.QWidget(), 1)
        layout.addWidget(widgets["bootMessage"], 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(QtWidgets.QWidget(), 1)

        layout = QtWidgets.QGridLayout(pages["home"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(panels["body"], 1, 0)
        layout.addWidget(widgets["extraContainer"], 4, 0)

        layout = QtWidgets.QVBoxLayout(pages["errored"])
        layout.addWidget(QtWidgets.QWidget(), 1)
        layout.addWidget(widgets["errorMessage"], 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(widgets["continue"], 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(widgets["reset"], 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(QtWidgets.QWidget(), 1)

        layout = QtWidgets.QVBoxLayout(pages["noapps"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(QtWidgets.QWidget(), 1)
        layout.addWidget(widgets["noappsMessage"], 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(QtWidgets.QWidget(), 1)

        #  _______________________________________________________
        # |          |         |         |               |        |
        # |   logo   | project |---------|               |--------|
        # |__________|_________|_________|_______________|________|
        #

        layout = QtWidgets.QGridLayout(panels["header"])
        layout.setHorizontalSpacing(px(10))
        layout.setVerticalSpacing(0)

        def addColumn(widgets, *args, **kwargs):
            """Convenience function for adding columns to GridLayout"""
            addColumn.row = getattr(addColumn, "row", -1)
            addColumn.row += kwargs.get("offset", 1)

            for row, widget in enumerate(widgets):
                layout.addWidget(widget, row, addColumn.row, *args)

            if kwargs.get("stretch"):
                layout.setColumnStretch(addColumn.row, 1)

        addColumn([widgets["projectBtn"]], 2, 1)
        addColumn([widgets["projectName"],
                   widgets["projectVersions"]])

        addColumn([QtWidgets.QWidget()], stretch=True)  # Spacing
        addColumn([widgets["dockToggles"]], 2, 1)

        addColumn([QtWidgets.QWidget()], stretch=True)  # Spacing

        addColumn([QtWidgets.QLabel("launchapp2"),
                   widgets["appVersion"]])
        addColumn([widgets["logo"]], 2, 1)  # spans 2 rows

        layout = QtWidgets.QHBoxLayout(widgets["dockToggles"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for name, dock in docks.items():
            toggle = QtWidgets.QPushButton()
            toggle.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                 QtWidgets.QSizePolicy.Expanding)
            toggle.setObjectName(name + "Toggle")
            toggle.setCheckable(True)
            toggle.setFlat(True)
            toggle.setProperty("type", "toggle")
            toggle.setToolTip("%s\n%s" % (type(dock).__name__, dock.__doc__ or ""))
            toggle.setIcon(res.pixmap(dock.icon))
            toggle.setIconSize(QtCore.QSize(px(32), px(32)))
            toggle.clicked.connect(
                lambda d=dock, t=toggle: d.setVisible(t.isChecked())
            )

            toggle.clicked.connect(
                lambda d=dock, t=toggle: self.on_dock_toggled(
                    d, t.isChecked())
            )

            # Store reference for showEvent
            dock.toggle = toggle

            # Create two-way connection; when dock is programatically
            # closed, or closed by other means, update toggle to reflect this.
            dock.visibilityChanged.connect(
                lambda s, d=dock, t=toggle: t.setChecked(d.isVisible())
            )

            layout.addWidget(toggle)

        layout = QtWidgets.QVBoxLayout(panels["body"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["apps"])

        layout = QtWidgets.QHBoxLayout(widgets["extraContainer"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QtWidgets.QWidget(), 1)
        layout.addWidget(widgets["extraRequirementsPrefix"])
        layout.addWidget(widgets["extraRequirements"])
        layout.addWidget(widgets["extraRequirementsSuffix"])
        layout.addWidget(QtWidgets.QWidget(), 1)  # centered

        status_bar = self.statusBar()
        status_bar.addPermanentWidget(widgets["stateIndicator"])

        # Setup
        widgets["logo"].setPixmap(res.pixmap("Logo_64"))
        widgets["logo"].setScaledContents(True)
        widgets["projectBtn"].setMenu(widgets["projectMenu"])
        widgets["projectBtn"].setPopupMode(widgets["projectBtn"].InstantPopup)
        widgets["projectBtn"].setIcon(res.pixmap("Default_Project"))
        widgets["projectBtn"].setIconSize(QtCore.QSize(px(32), px(32)))

        widgets["projectVersions"].setModel(ctrl.models["projectVersions"])
        widgets["extraRequirements"].setMinimumWidth(10)
        widgets["extraRequirements"].setPlaceholderText("<requirements>")

        def resize_to_content():
            lineedit = widgets["extraRequirements"]
            font = QtGui.QFont("", 0)
            fm = QtGui.QFontMetrics(font)
            pixelsWide = fm.width(lineedit.text())
            lineedit.setMinimumWidth(pixelsWide)

        widgets["extraRequirements"].textChanged.connect(resize_to_content)

        docks["packages"].set_model(ctrl.models["packages"])
        docks["context"].set_model(ctrl.models["context"])
        docks["environment"].set_model(ctrl.models["environment"])
        docks["commands"].set_model(ctrl.models["commands"])
        widgets["apps"].setModel(ctrl.models["apps"])

        tool_group = actions["launchToolsGroup"]
        tool_group.triggered.connect(self.on_tool_changed)

        widgets["projectMenu"].aboutToShow.connect(self.on_show_project_menu)
        widgets["extraContainer"].hide()
        widgets["extraRequirements"].editingFinished.connect(
            self.on_extra_requirements_edited)

        widgets["errorMessage"].setAlignment(QtCore.Qt.AlignHCenter)

        # Signals
        widgets["reset"].clicked.connect(self.on_reset_clicked)
        widgets["continue"].clicked.connect(self.on_continue_clicked)
        widgets["apps"].activated.connect(self.on_app_clicked)
        widgets["projectName"].setText(ctrl.current_project)
        selection_model = widgets["apps"].selectionModel()
        selection_model.selectionChanged.connect(self.on_app_changed)

        ctrl.models["apps"].modelReset.connect(self.on_apps_reset)
        ctrl.models["projectVersions"].modelReset.connect(
            self.on_project_versions_reset)
        ctrl.state_changed.connect(self.on_state_changed)
        ctrl.logged.connect(self.on_logged)
        ctrl.project_changed.connect(self.on_project_changed)

        self._pages = pages
        self._widgets = widgets
        self._panels = panels
        self._docks = docks
        self._actions = actions
        self._ctrl = ctrl

        # self.setup_menus()
        self.setup_docks()
        self.on_state_changed("booting")

    def createPopupMenu(self):
        """Null; defaults to checkboxes for docks and toolbars"""

    def setup_menus(self):
        bar = self.menuBar()
        menu = bar.addMenu("&File")
        menu = bar.addMenu("&Advanced")

        toggles = (
            ("Show Context", "context"),
            ("Show Packages", "console"),
            ("Show Environment", "environment"),
            ("Show Console", "packages"),
        )

        for label, dock in toggles:
            action = QtWidgets.QAction(label, bar)
            action.setCheckable(True)
            action.setChecked(True)

            action.setToolTip(dock.__doc__)

            action.activated.connect(
                lambda d=dock, a=action:
                self._docks[d].setVisible(a.isChecked())
            )

            menu.addAction(action)

        menu.addSeparator()

        developer_mode = QtWidgets.QAction("Developer Mode", bar)
        developer_mode.setCheckable(True)
        menu.addAction(developer_mode)

        menu = bar.addMenu("&Help")

    def on_tool_changed(self, action):
        self.tell("%s triggered" % action.text())
        tool = action.text()
        self._ctrl.select_tool(tool)

    def on_extra_requirements_checked(self):
        action = self._actions["extraRequirements"]
        self._widgets["extraContainer"].setVisible(action.isChecked())

        if action.isChecked():
            self.on_extra_requirements_edited()
        else:
            self._ctrl.edit_requirements([])

    def on_extra_requirements_edited(self):
        requirements = self._widgets["extraRequirements"].text()
        self._ctrl.edit_requirements(requirements.split())

    def setup_docks(self):
        for dock in self._docks.values():
            dock.hide()

        self.setTabPosition(QtCore.Qt.RightDockWidgetArea,
                            QtWidgets.QTabWidget.North)
        self.setTabPosition(QtCore.Qt.LeftDockWidgetArea,
                            QtWidgets.QTabWidget.North)

        area = QtCore.Qt.RightDockWidgetArea
        first = list(self._docks.values())[0]
        self.addDockWidget(area, first)

        for dock in self._docks.values():
            if dock is first:
                continue

            self.addDockWidget(area, dock)
            self.tabifyDockWidget(first, dock)

    def reset(self):
        self._ctrl.reset()

    def on_reset_clicked(self):
        self.reset()

    def on_continue_clicked(self):
        self._ctrl.state.to_ready()

    def on_dock_toggled(self, dock, visible):
        """Make toggled dock the active dock"""

        if not visible:
            return

        # Handle the easy cases first
        app = QtWidgets.QApplication.instance()
        ctrl_held = app.keyboardModifiers() & QtCore.Qt.ControlModifier
        allow_multiple = int(self._ctrl.state.retrieve("allowMultipleDocks"))

        if ctrl_held or not allow_multiple:
            for d in self._docks.values():
                d.setVisible(d == dock)
            return

        # Otherwise we'll want to make the newly visible dock the active tab.

        # Turns out to not be that easy
        # https://forum.qt.io/topic/42044/
        # tabbed-qdockwidgets-how-to-fetch-the-qwidgets-under-a-qtabbar/10

        # TabBar's are dynamically created as the user
        # moves docks around, and not all of them are
        # visible or in use at all times. (Poor garbage collection)
        bars = self.findChildren(QtWidgets.QTabBar)

        # The children of a QTabBar isn't the dock directly, but rather
        # the buttons in the tab, which are of type QToolButton.

        uid = dock.windowTitle()  # note: This must be unique

        # Find which tab is associated to this QDockWidget, if any
        def find_dock(bar):
            for index in range(bar.count()):
                if uid == bar.tabText(index):
                    return index

        for bar in bars:
            index = find_dock(bar)

            if index is not None:
                break
        else:
            # Dock isn't part of any tab and is directly visible
            return

        bar.setCurrentIndex(index)

    def on_show_project_menu(self):
        self.tell("Changing project..")

        all_projects = self._ctrl.list_projects()
        current_project = self._ctrl.current_project

        def on_accept(project):
            project = project.text()
            assert isinstance(project, six.string_types)

            self._ctrl.select_project(project)
            self._ctrl.state.store("startupProject", project)

        menu = self._widgets["projectMenu"]
        menu.clear()

        group = QtWidgets.QActionGroup(menu)
        group.triggered.connect(on_accept)

        for project in all_projects:
            action = QtWidgets.QAction(project, menu)
            action.setCheckable(True)

            if project == current_project:
                action.setChecked(True)

            group.addAction(action)
            menu.addAction(action)

    def on_show_tools_menu(self):
        tool_group = self._actions["launchToolsGroup"]

        # for action in tool_group.actions():
        #     tool_group.removeAction(action)

        # app_name = self._ctrl.current_application
        # for tool in self._ctrl.tools(app_name):
        #     cmd = QtWidgets.QAction(tool, self)
        #     cmd.setCheckable(True)

        #     if tool == self._ctrl.current_tool:
        #         cmd.setChecked(True)

        #     tool_group.addAction(cmd)
        #     menu.addAction(cmd)

        # menu.addSeparator()

        # extra = self._actions["extraRequirements"]
        # extra.triggered.connect(self.on_extra_requirements_checked)
        # extra.setCheckable(True)
        # menu.addAction(extra)

    def on_project_changed(self, before, after):
        # Happens when editing requirements
        if before != after:
            action = "Changing"
        else:
            action = "Refreshing"

        self.tell("%s %s -> %s" % (action, before, after))
        self.setWindowTitle("%s - %s" % (self.title, after))
        self._widgets["projectName"].setText(after)

    def on_show_error(self):
        self._docks["console"].append(self._ctrl.current_error)
        self._docks["console"].raise_()

    def tell(self, message):
        self._docks["console"].append(message, logging.INFO)
        self.statusBar().showMessage(message, timeout=2000)

    def on_logged(self, message, level):
        self._docks["console"].append(message, level)

    def on_state_changed(self, state):
        self.tell("State: %s" % state)

        page = self._pages.get(str(state), self._pages["home"])
        page_name = page.objectName()
        self._panels["pages"].setCurrentWidget(page)

        launch_btn = self._docks["app"]._widgets["launchBtn"]
        launch_btn.setText("Launch")

        for dock in self._docks.values():
            dock.setEnabled(True)

        if page_name == "home":
            self._widgets["apps"].setEnabled(state == "ready")
            self._widgets["projectBtn"].setEnabled(state == "ready")
            self._widgets["projectVersions"].setEnabled(state == "ready")

        elif page_name == "noapps":
            self._widgets["projectBtn"].setEnabled(True)
            self._widgets["noappsMessage"].setText(
                "No applications found for %s" % self._ctrl.current_project
            )

        if state == "launching":
            self._docks["app"].setEnabled(False)

        if state == "loading":
            for dock in self._docks.values():
                dock.setEnabled(False)

        if state in ("pkgnotfound", "errored"):
            console = self._docks["console"]
            console.show()
            self.on_dock_toggled(console, visible=True)

            page = self._pages["errored"]
            self._panels["pages"].setCurrentWidget(page)

            self._widgets["apps"].setEnabled(False)
            launch_btn.setEnabled(False)
            launch_btn.setText("Package not found")

        if state == "notresolved":
            self._widgets["apps"].setEnabled(False)
            launch_btn.setEnabled(False)
            launch_btn.setText("Failed to resolve")

        self._widgets["stateIndicator"].setText(str(state))

    def on_launch_clicked(self):
        self._ctrl.launch()

    def on_project_versions_reset(self):
        self._widgets["projectVersions"].setCurrentIndex(0)

    def on_apps_reset(self):
        app = self._ctrl.state.retrieve("startupApplication")

        index = 0
        model = self._ctrl.models["apps"]

        if app:
            for row in range(model.rowCount()):
                index = model.index(row, 0, QtCore.QModelIndex())
                name = index.data(QtCore.Qt.DisplayRole)

                if app == name:
                    index = row
                    self.tell("Using startup application %s" % name)
                    break

        self._widgets["apps"].selectRow(index)

    def on_app_clicked(self, index):
        """An app was double-clicked or Return was hit"""

        app = self._docks["app"]
        app.show()
        self.on_dock_toggled(app, visible=True)

    def on_app_changed(self, selected, deselected):
        """The current app was changed

        Arguments:
            selected (QtCore.QItemSelection): ..
            deselected (QtCore.QItemSelection): ..

        """

        index = selected.indexes()[0]
        app_name = index.data(QtCore.Qt.DisplayRole)
        self._ctrl.select_application(app_name)

        project = self._ctrl.current_project
        app = self._ctrl.current_application
        tool = self._ctrl.current_tool

        self._widgets["extraRequirementsPrefix"].setText(
            "rez env %s %s " % (project, app))
        self._widgets["extraRequirementsSuffix"].setText(" -- %s" % tool)

        self._docks["app"].refresh(index)

    def showEvent(self, event):
        super(Window, self).showEvent(event)
        self._ctrl.state.store("default/geometry", self.saveGeometry())
        self._ctrl.state.store("default/windowState", self.saveState())

        if self._ctrl.state.retrieve("geometry"):
            self.tell("Restoring layout..")
            self.restoreGeometry(self._ctrl.state.retrieve("geometry"))
            self.restoreState(self._ctrl.state.retrieve("windowState"))

            if self._ctrl.state.retrieve("extraRequirements"):
                self._actions["extraRequirements"].setChecked(True)
                self._actions["extraRequirements"].triggered.emit()

    def closeEvent(self, event):
        self.tell("Storing state..")
        self._ctrl.state.store("geometry", self.saveGeometry())
        self._ctrl.state.store("windowState", self.saveState())

        if self._actions["extraRequirements"].isChecked():
            self._ctrl.state.store("extraRequirements", True)

        super(Window, self).closeEvent(event)


class ProjectBrowser(QtWidgets.QDialog):
    accepted = QtCore.Signal(str)  # project
    declined = QtCore.Signal()

    def __init__(self, current, projects, parent=None):
        super(ProjectBrowser, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Popup)
        self.setWindowTitle("Projects..")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        widgets = {
            "listing": QtWidgets.QListWidget(),
        }

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["listing"])

        for row, project in enumerate(projects):
            QtWidgets.QListWidgetItem(project, widgets["listing"])

            if project == current:
                widgets["listing"].setCurrentRow(row)

        widgets["listing"].itemClicked.connect(self.accept)
        widgets["listing"].itemActivated.connect(self.accept)

        self._widgets = widgets

    def setFocus(self, reason=None):
        """Focus means focus on the listing itself"""
        self._widgets["listing"].setFocus()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            return self.accept()

        # ESC is natively associated with hideEvent
        super(ProjectBrowser, self).keyPressEvent(event)

    def accept(self, item=None):
        if not item:
            listing = self._widgets["listing"]
            item = listing.selectedItems()[0]
        self.accepted.emit(item.text())
        self.close()

    def decline(self):
        self.declined.emit()
        self.close()

    def hideEvent(self, event):
        self.decline()


class DockWidget(QtWidgets.QDockWidget):
    """Default HTML <b>docs</b>"""

    icon = ""

    def __init__(self, title, parent=None):
        super(DockWidget, self).__init__(title, parent)
        self.layout().setContentsMargins(15, 15, 15, 15)

        panels = {
            "body": QtWidgets.QStackedWidget(),
            "help": QtWidgets.QLabel(),
        }

        for name, widget in panels.items():
            widget.setObjectName(name)

        central = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
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


class App(DockWidget):
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

        layout.addWidget(widgets["icon"], 0, 0, 2, 1)
        layout.addWidget(widgets["label"], 0, 1, QtCore.Qt.AlignTop)
        layout.addWidget(widgets["tool"], 1, 1, QtCore.Qt.AlignTop)
        # layout.addWidget(QtWidgets.QWidget(), 0, 1, 1, 1)
        # layout.addWidget(widgets["version"], 1, 1, QtCore.Qt.AlignTop)
        layout.addWidget(widgets["commands"], 2, 0, 1, 2)
        # layout.addWidget(widgets["extras"], 3, 0, 1, 2)
        # layout.addWidget(panels["shortcuts"], 10, 0, 1, 2)
        layout.addWidget(QtWidgets.QWidget(), 15, 0)
        # layout.setColumnStretch(1, 1)
        layout.setRowStretch(15, 1)
        layout.addWidget(panels["footer"], 20, 0, 1, 2)

        widgets["icon"].setPixmap(res.pixmap("Alert_Info_32"))
        widgets["environment"].setIcon(res.pixmap(Environment.icon))
        widgets["packages"].setIcon(res.pixmap(Packages.icon))
        widgets["terminal"].setIcon(res.pixmap(Console.icon))
        widgets["tool"].setText("maya")

        for sc in ("environment", "packages", "terminal"):
            widgets[sc].setIconSize(QtCore.QSize(px(32), px(32)))

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

    def refresh(self, index):
        name = index.data(QtCore.Qt.DisplayRole)
        icon = index.data(QtCore.Qt.DecorationRole)
        icon = icon.pixmap(QtCore.QSize(px(64), px(64)))
        self._widgets["label"].setText(name)
        self._widgets["icon"].setPixmap(icon)

        self._proxy.setup(include=[
            ("appName", name),
            ("running", "running"),
        ])


class Console(DockWidget):
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
        widgets["text"].setLineWrapMode(widgets["text"].NoWrap)

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


class Packages(DockWidget):
    """Packages associated with the currently selected application"""

    icon = "File_Archive_32"

    def __init__(self, ctrl, parent=None):
        super(Packages, self).__init__("Packages", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Packages")

        panels = {
            "central": QtWidgets.QWidget()
        }

        widgets = {
            "view": SlimTableView(),
        }

        self.setWidget(panels["central"])

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["view"])

        widgets["view"].setStretch(1)
        widgets["view"].setItemDelegate(delegates.Package(ctrl, self))
        widgets["view"].setEditTriggers(widgets["view"].DoubleClicked)
        widgets["view"].verticalHeader().setDefaultSectionSize(px(20))
        widgets["view"].setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        widgets["view"].customContextMenuRequested.connect(self.on_right_click)

        self._ctrl = ctrl
        self._widgets = widgets

    def set_model(self, model):
        self._widgets["view"].setModel(model)

    def on_right_click(self, position):
        view = self._widgets["view"]
        index = view.indexAt(position)

        menu = QtWidgets.QMenu(self)
        edit = QtWidgets.QAction("Edit")
        default = QtWidgets.QAction("Set to default")
        latest = QtWidgets.QAction("Set to latest")
        earliest = QtWidgets.QAction("Set to earliest")

        menu.addAction(edit)
        menu.addAction(default)
        menu.addAction(latest)
        menu.addAction(earliest)
        menu.move(QtGui.QCursor.pos())

        picked = menu.exec_()

        if picked is None:
            return  # Cancelled

        if picked == edit:
            self._widgets["view"].edit(index)

        if picked == default:
            model = index.model()
            model.setData(index, None, "override")

        if picked == earliest:
            model = index.model()
            versions = model.data(index, "versions")
            model.setData(index, versions[0], "override")

        if picked == latest:
            model = index.model()
            versions = model.data(index, "versions")
            model.setData(index, versions[-1], "override")


class Context(DockWidget):
    """Full context relative the currently selected application"""

    icon = "App_Generic_4_32"

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

        self.setWidget(panels["central"])

    def set_model(self, model):
        self._widgets["view"].setModel(model)


class Environment(DockWidget):
    """Full environment relative the currently selected application"""

    icon = "App_Heidi_32"

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

        self.setWidget(panels["central"])

    def set_model(self, model):
        self._widgets["view"].setModel(model)


class Commands(DockWidget):
    """Currently running commands"""

    icon = "App_Pulse_32"

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
            "stdout": QtWidgets.QTextEdit(),
            "stderr": QtWidgets.QTextEdit(),
        }

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(panels["body"])
        # layout.addWidget(panels["footer"])

        layout = QtWidgets.QVBoxLayout(panels["body"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["view"])

        layout = QtWidgets.QVBoxLayout(panels["footer"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["stdout"])
        layout.addWidget(widgets["stderr"])

        self._panels = panels
        self._widgets = widgets

        self.setWidget(panels["central"])

    def set_model(self, model):
        self._widgets["view"].setModel(model)


class _Option(dict):
    def __init__(self, name, **kwargs):
        super(_Option, self).__init__(name=name, **kwargs)

        self["label"] = name


class Boolean(_Option):
    pass


class String(_Option):
    pass


class Info(_Option):
    pass


class Color(_Option):
    pass


class Button(_Option):
    pass


class Preferences(DockWidget):
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
        qargparse.Boolean("developerMode", enabled=False, help=(
            "Show developer-centric controls"
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
        if argument["name"] == "resetLayout":
            self._window.tell("Restoring layout..")
            geometry = self._ctrl.state.retrieve("default/geometry")
            window = self._ctrl.state.retrieve("default/windowState")
            self._window.restoreGeometry(geometry)
            self._window.restoreState(window)

        else:
            self._window.tell("Storing %s = %s" % (argument["name"],
                                                   argument.read()))
            self._ctrl.state.store(argument["name"], argument.read())


class SlimTableView(QtWidgets.QTableView):
    def __init__(self, parent=None):
        super(SlimTableView, self).__init__(parent)
        self.setShowGrid(False)
        self.verticalHeader().hide()
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)
        self._stretch = 0

    def setStretch(self, column):
        self._stretch = column

    def refresh(self):
        header = self.horizontalHeader()
        QtCompat.setSectionResizeMode(
            header, self._stretch, QtWidgets.QHeaderView.Stretch)

    def setModel(self, model):
        model.rowsInserted.connect(self.refresh)
        model.modelReset.connect(self.refresh)
        super(SlimTableView, self).setModel(model)
        self.refresh()
