"""The view may access a controller, but not vice versa"""

import os
import logging

from itertools import chain
from functools import partial
from collections import OrderedDict as odict

from .vendor.Qt import QtWidgets, QtCore, QtGui
from .vendor import six, qargparse
from .version import version
from . import resources as res, dock

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

            "apps": dock.SlimTableView(),

            # Error page
            "continue": QtWidgets.QPushButton("Continue"),
            "reset": QtWidgets.QPushButton("Reset"),

            "dockToggles": QtWidgets.QWidget(),

            "stateIndicator": QtWidgets.QLabel(),
        }

        # The order is reflected in the UI
        docks = odict((
            ("app", dock.App(ctrl)),
            ("packages", dock.Packages(ctrl)),
            ("context", dock.Context()),
            ("environment", dock.Environment()),
            ("console", dock.Console()),
            ("commands", dock.Commands()),
            ("preferences", dock.Preferences(self, ctrl)),
        ))

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

        for name, widget in docks.items():
            toggle = QtWidgets.QPushButton()
            toggle.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                 QtWidgets.QSizePolicy.Expanding)
            toggle.setObjectName(name + "Toggle")
            toggle.setCheckable(True)
            toggle.setFlat(True)
            toggle.setProperty("type", "toggle")
            toggle.setIcon(res.icon(widget.icon))
            toggle.setIconSize(QtCore.QSize(px(32), px(32)))
            toggle.setToolTip("\n".join([
                type(widget).__name__, widget.__doc__ or ""]))

            def on_toggled(widget, toggle):
                widget.setVisible(toggle.isChecked())
                self.on_dock_toggled(widget, toggle.isChecked())

            def on_visible(widget, toggle, state):
                toggle.setChecked(widget.isVisible())

            toggle.clicked.connect(partial(on_toggled, widget, toggle))

            # Store reference for showEvent
            widget.toggle = toggle

            # Store reference for update_advanced_controls
            toggle.dock = widget

            # Create two-way connection; when widget is programatically
            # closed, or closed by other means, update toggle to reflect this.
            widget.visibilityChanged.connect(
                partial(on_visible, widget, toggle))

            # Forward any messages
            widget.message.connect(self.tell)

            layout.addWidget(toggle)

        layout = QtWidgets.QVBoxLayout(panels["body"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["apps"])

        status_bar = self.statusBar()
        status_bar.addPermanentWidget(widgets["stateIndicator"])

        # Setup
        widgets["logo"].setPixmap(res.pixmap("Logo_64"))
        widgets["logo"].setScaledContents(True)
        widgets["projectBtn"].setMenu(widgets["projectMenu"])
        widgets["projectBtn"].setPopupMode(widgets["projectBtn"].InstantPopup)
        widgets["projectBtn"].setIcon(res.icon("Default_Project"))
        widgets["projectBtn"].setIconSize(QtCore.QSize(px(32), px(32)))

        widgets["projectVersions"].setModel(ctrl.models["projectVersions"])

        docks["packages"].set_model(ctrl.models["packages"])
        docks["context"].set_model(ctrl.models["context"])
        docks["environment"].set_model(ctrl.models["environment"])
        docks["commands"].set_model(ctrl.models["commands"])
        widgets["apps"].setModel(ctrl.models["apps"])

        widgets["projectMenu"].aboutToShow.connect(self.on_show_project_menu)
        widgets["errorMessage"].setAlignment(QtCore.Qt.AlignHCenter)

        # Signals
        widgets["reset"].clicked.connect(self.on_reset_clicked)
        widgets["continue"].clicked.connect(self.on_continue_clicked)
        widgets["apps"].activated.connect(self.on_app_clicked)
        widgets["projectName"].setText(ctrl.current_project)

        widgets["apps"].setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        widgets["apps"].customContextMenuRequested.connect(self.on_app_right_click)

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
        self._ctrl = ctrl

        self.setup_docks()
        self.on_state_changed("booting")
        self.update_advanced_controls()

        # Enable mouse tracking for tooltips
        QtWidgets.QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        """Forward tooltips to status bar whenever the mouse moves"""
        if event.type() == QtCore.QEvent.MouseMove:
            try:
                tooltip = obj.toolTip()

                # Some tooltips are multi-line, and the statusbar
                # typically ignores newlines and writes it all out
                # as one long line.
                tooltip = tooltip.splitlines()[0]

                self.statusBar().showMessage(tooltip, 2000)
            except (AttributeError, IndexError):
                pass

        # Forward the event to subsequent listeners
        return False

    def createPopupMenu(self):
        """Null; defaults to checkboxes for docks and toolbars"""

    def update_advanced_controls(self):
        shown = bool(self._ctrl.state.retrieve("showAdvancedControls"))
        self._widgets["projectVersions"].setVisible(shown)

        # Update dock toggles
        toggles = self._widgets["dockToggles"].layout()
        for index in range(toggles.count()):
            item = toggles.itemAt(index)
            widget = item.widget()
            dock = widget.dock

            visible = (not dock.advanced) or shown
            widget.setVisible(visible)

            if not visible:
                dock.hide()

    def setup_docks(self):
        for widget in self._docks.values():
            widget.hide()

        self.setTabPosition(QtCore.Qt.RightDockWidgetArea,
                            QtWidgets.QTabWidget.North)
        self.setTabPosition(QtCore.Qt.LeftDockWidgetArea,
                            QtWidgets.QTabWidget.North)

        area = QtCore.Qt.RightDockWidgetArea
        first = list(self._docks.values())[0]
        self.addDockWidget(area, first)

        for widget in self._docks.values():
            if widget is first:
                continue

            self.addDockWidget(area, widget)
            self.tabifyDockWidget(first, widget)

    def reset(self):
        self._ctrl.reset()

    def on_command_copied(self, cmd):
        self.tell("Copied command '%s'" % cmd)

    def on_reset_clicked(self):
        self.reset()

    def on_continue_clicked(self):
        self._ctrl.state.to_ready()

    def on_app_right_click(self, position):
        menu = QtWidgets.QMenu(self)
        open_in_cmd = QtWidgets.QAction("Open in cmd.exe", menu)
        open_in_powershell = QtWidgets.QAction("Open in PowerShell", menu)
        open_in_bash = QtWidgets.QAction("Open in Bash", menu)

        if os.name == "nt":
            menu.addAction(open_in_cmd)
            menu.addAction(open_in_powershell)
        else:
            menu.addAction(open_in_bash)

        menu.move(QtGui.QCursor.pos())

        picked = menu.exec_()

        if picked is None:
            return  # Cancelled

        if picked == open_in_cmd:
            self._ctrl.launch(command="start cmd")

        if picked == open_in_powershell:
            self._ctrl.launch(command="start powershell")

        if picked == open_in_bash:
            self._ctrl.launch(command="bash")

    def on_setting_changed(self, argument):
        if isinstance(argument, qargparse.Button):
            if argument["name"] == "resetLayout":
                self.tell("Restoring layout..")
                geometry = self._ctrl.state.retrieve("default/geometry")
                window = self._ctrl.state.retrieve("default/windowState")
                self.restoreGeometry(geometry)
                self.restoreState(window)
            return

        key = argument["name"]
        value = argument.read()

        self.tell("Storing %s = %s" % (key, value))
        self._ctrl.state.store(argument["name"], argument.read())

        # Subsequent settings are stored to disk
        if key == "showAdvancedControls":
            self.update_advanced_controls()

    def on_dock_toggled(self, dock, visible):
        """Make toggled dock the active dock"""

        if not visible:
            return

        # Handle the easy cases first
        app = QtWidgets.QApplication.instance()
        ctrl_held = app.keyboardModifiers() & QtCore.Qt.ControlModifier
        allow_multiple = bool(self._ctrl.state.retrieve("allowMultipleDocks"))

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
        self.statusBar().showMessage(message, 2000)

    def on_logged(self, message, level):
        self._docks["console"].append(message, level)

    def on_state_changed(self, state):
        self.tell("State: %s" % state)

        page = self._pages.get(str(state), self._pages["home"])
        page_name = page.objectName()
        self._panels["pages"].setCurrentWidget(page)

        launch_btn = self._docks["app"]._widgets["launchBtn"]
        launch_btn.setText("Launch")

        for widget in self._docks.values():
            widget.setEnabled(True)

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
            for widget in self._docks.values():
                widget.setEnabled(False)

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
        self.update_advanced_controls()

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
                name = model.data(index, "name")

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
        model = index.model()
        app_name = model.data(index, "name")
        self._ctrl.select_application(app_name)
        self._docks["app"].refresh(index)

    def showEvent(self, event):
        super(Window, self).showEvent(event)
        self._ctrl.state.store("default/geometry", self.saveGeometry())
        self._ctrl.state.store("default/windowState", self.saveState())

        if self._ctrl.state.retrieve("geometry"):
            self.tell("Restoring layout..")
            self.restoreGeometry(self._ctrl.state.retrieve("geometry"))
            self.restoreState(self._ctrl.state.retrieve("windowState"))

    def closeEvent(self, event):
        self.tell("Storing state..")
        self._ctrl.state.store("geometry", self.saveGeometry())
        self._ctrl.state.store("windowState", self.saveState())

        super(Window, self).closeEvent(event)
