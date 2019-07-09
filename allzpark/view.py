"""The view may access a controller, but not vice versa"""

import os
import logging

from itertools import chain
from functools import partial
from collections import OrderedDict as odict

from .vendor.Qt import QtWidgets, QtCore, QtGui
from .vendor import six, qargparse
from .version import version
from . import resources as res, dock, model

px = res.px


class Window(QtWidgets.QMainWindow):
    title = "Allzpark"

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
            ("loading", QtWidgets.QWidget()),
            ("errored", QtWidgets.QWidget()),
            ("noapps", QtWidgets.QWidget()),
            ("noproject", QtWidgets.QWidget()),
        ))

        panels = {
            "pages": QtWidgets.QStackedWidget(),
            "header": QtWidgets.QWidget(),
            "body": QtWidgets.QWidget(),
            "footer": QtWidgets.QWidget(),
        }

        widgets = {
            "bootMessage": QtWidgets.QLabel("Loading.."),
            "loadingMessage": QtWidgets.QLabel("Loading"),
            "errorMessage": QtWidgets.QLabel("Uh oh..<br>"
                                             "See Console for details"),
            "noappsMessage": QtWidgets.QLabel("No applications found"),
            "noprojectMessage": QtWidgets.QLabel("No project found"),
            "pkgnotfoundMessage": QtWidgets.QLabel(
                "One or more packages could not be found"
            ),

            # Header
            "logo": QtWidgets.QLabel(),
            "appVersion": QtWidgets.QLabel(version),

            "projectBtn": QtWidgets.QToolButton(),
            "projectMenu": QtWidgets.QMenu(),
            "projectName": LineEditWithCompleter(),
            "projectVersion": LineEditWithCompleter(),

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
        layout = QtWidgets.QGridLayout(pages["home"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(panels["body"], 1, 0)

        layout = QtWidgets.QVBoxLayout(pages["booting"])
        layout.addWidget(QtWidgets.QWidget(), 1)
        layout.addWidget(widgets["bootMessage"], 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(QtWidgets.QWidget(), 1)

        layout = QtWidgets.QVBoxLayout(pages["loading"])
        layout.addWidget(QtWidgets.QWidget(), 1)
        layout.addWidget(widgets["loadingMessage"], 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(QtWidgets.QWidget(), 1)

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

        layout = QtWidgets.QVBoxLayout(pages["noproject"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(QtWidgets.QWidget(), 1)
        layout.addWidget(widgets["noprojectMessage"], 0, QtCore.Qt.AlignHCenter)
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
                   widgets["projectVersion"]])

        addColumn([QtWidgets.QWidget()], stretch=True)  # Spacing
        addColumn([widgets["dockToggles"]], 2, 1)

        addColumn([QtWidgets.QWidget()], stretch=True)  # Spacing

        addColumn([QtWidgets.QLabel("allzpark"),
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
        widgets["projectBtn"].setToolTip("Click to change project")
        widgets["projectBtn"].clicked.connect(self.on_projectbtn_pressed)
        widgets["projectBtn"].setIcon(res.icon("Default_Project"))
        widgets["projectBtn"].setIconSize(QtCore.QSize(px(32), px(32)))

        widgets["projectBtn"].setCursor(QtCore.Qt.PointingHandCursor)
        widgets["projectName"].setCursor(QtCore.Qt.PointingHandCursor)
        widgets["projectVersion"].setCursor(QtCore.Qt.PointingHandCursor)

        widgets["projectName"].setToolTip("Click to change project")
        widgets["projectName"].setModel(ctrl.models["projectNames"])
        widgets["projectVersion"].setToolTip("Click to change project version")
        widgets["projectVersion"].setModel(ctrl.models["projectVersions"])

        docks["packages"].set_model(ctrl.models["packages"])
        docks["context"].set_model(ctrl.models["context"])
        docks["environment"].set_model(ctrl.models["environment"])
        docks["commands"].set_model(ctrl.models["commands"])

        proxy_model = model.ProxyModel(ctrl.models["apps"])
        widgets["apps"].setModel(proxy_model)

        # widgets["projectMenu"].aboutToShow.connect(self.on_show_project_menu)
        widgets["errorMessage"].setAlignment(QtCore.Qt.AlignHCenter)

        # Signals
        widgets["projectName"].editingFinished.connect(
            self.on_projectname_suggested)
        completer = widgets["projectName"].completer()
        completer.activated.connect(self.on_projectname_completed)

        widgets["reset"].clicked.connect(self.on_reset_clicked)
        widgets["continue"].clicked.connect(self.on_continue_clicked)
        widgets["apps"].activated.connect(self.on_app_clicked)

        widgets["apps"].customContextMenuRequested.connect(
            self.on_app_right_click)

        selection_model = widgets["apps"].selectionModel()
        selection_model.selectionChanged.connect(self.on_app_changed)

        ctrl.models["apps"].modelReset.connect(self.on_apps_reset)
        ctrl.models["projectNames"].modelReset.connect(
            self.on_projectname_reset)
        ctrl.models["projectVersions"].modelReset.connect(
            self.on_projectversion_reset)
        ctrl.resetted.connect(self.on_reset)
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
                self.statusBar().clearMessage()

        # Forward the event to subsequent listeners
        return False

    def createPopupMenu(self):
        """Null; defaults to checkboxes for docks and toolbars"""

    def update_advanced_controls(self):
        shown = bool(self._ctrl.state.retrieve("showAdvancedControls"))
        self._widgets["projectVersion"].setVisible(shown)

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

    def on_reset(self):
        pass

    def on_command_copied(self, cmd):
        self.tell("Copied command '%s'" % cmd)

    def on_reset_clicked(self):
        self.reset()

    def on_continue_clicked(self):
        self._ctrl.state.to_ready()

    def on_app_right_click(self, position):
        view = self._widgets["apps"]
        index = view.indexAt(position)

        if not index.isValid():
            # Clicked outside any item
            return

        model = index.model()
        tools = model.data(index, "tools")

        menu = QtWidgets.QMenu(self)

        separator = QtWidgets.QWidgetAction(menu)
        separator.setDefaultWidget(QtWidgets.QLabel("Quick Launch"))
        menu.addAction(separator)

        for tool in tools:
            menu.addAction(QtWidgets.QAction(tool, menu))

        menu.addSeparator()

        extras = (
            ["start cmd", "start powershell"]
            if os.name == "nt" else
            ["bash"]
        )

        for tool in extras:
            menu.addAction(QtWidgets.QAction(tool, menu))

        menu.move(QtGui.QCursor.pos())

        picked = menu.exec_()

        if picked is None:
            return  # Cancelled

        self._ctrl.launch(command=picked.text())

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

        if key == "showAllApps":
            self._ctrl.reset()

        if key == "showHiddenApps":
            self._ctrl.reset()

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

    def on_projectname_suggested(self):
        widget = self._widgets["projectName"]
        widget.parent().setFocus()  # Double-tab Tab to return

    def on_projectname_clicked(self):
        pass

    def on_projectname_completed(self, project):
        if self._ctrl.current_project == project:
            return

        self._ctrl.select_project(project)
        self._ctrl.state.store("startupProject", project)

        self.setFocus()

    def on_projectversion_changed(self, index):
        pass

    def on_projectbtn_pressed(self):
        widget = self._widgets["projectName"]
        widget.setFocus()
        widget.selectAll()

        completer = widget.completer()
        completer.complete()

    def on_project_changed(self, before, after):
        # Happens when editing requirements
        if before != after:
            action = "Changing"
        else:
            action = "Refreshing"

        self.tell("%s %s -> %s" % (action, before, after))
        self.setWindowTitle("%s - %s" % (self.title, after))
        self._widgets["projectName"].setText(after)

        versions = self._ctrl.models["projectVersions"].stringList()

        try:
            version = versions[-1]
        except IndexError:
            # Package may not exist, thus have no versions
            version = ""

        self._widgets["projectVersion"].setText(version)

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
            self._widgets["projectVersion"].setEnabled(state == "ready")

        elif page_name == "noapps":
            self._widgets["projectBtn"].setEnabled(True)
            self._widgets["noappsMessage"].setText(
                "No apps was found for '%s'\n"
                "Check your REZ_PACKAGES_PATH" % self._ctrl.current_project
            )

        elif page_name == "noproject":
            self._widgets["projectBtn"].setEnabled(True)
            self._widgets["noprojectMessage"].setText(
                "No Rez package was found for project '%s'\n"
                "Check your REZ_PACKAGES_PATH" % self._ctrl.current_project
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

    def on_projectname_reset(self):
        print("Projects changed")

    def on_projectversion_reset(self):
        print("Versions changed")

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


class LineEditWithCompleter(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(LineEditWithCompleter, self).__init__(parent)

        proxy = QtCore.QSortFilterProxyModel(self)
        proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        completer = QtWidgets.QCompleter(proxy, self)
        completer.setCompletionMode(
            QtWidgets.QCompleter.UnfilteredPopupCompletion
        )

        self.setCompleter(completer)

        self._completer = completer
        self._proxy = proxy

    def setModel(self, model):
        self._proxy.setSourceModel(model)
        self._completer.setModel(self._proxy)

    def mousePressEvent(self, event):
        super(LineEditWithCompleter, self).mousePressEvent(event)

        self._completer.complete()
        self.selectAll()
