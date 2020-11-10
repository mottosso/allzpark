"""The view may access a controller, but not vice versa"""

import os
import logging

from itertools import chain
from functools import partial
from collections import OrderedDict as odict

from .vendor.Qt import QtWidgets, QtCore, QtGui
from .vendor import qargparse
from .version import version
from . import resources as res, dock, model
from . import allzparkconfig

px = res.px


class Window(QtWidgets.QMainWindow):
    title = "Allzpark %s" % version

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
            ("noprofiles", QtWidgets.QWidget()),
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
            "noappsMessage": QtWidgets.QTextBrowser(),
            "noprofileMessage": QtWidgets.QLabel("No profiles was found"),
            "pkgnotfoundMessage": QtWidgets.QLabel(
                "One or more packages could not be found"
            ),

            # Header
            "logo": QtWidgets.QToolButton(),
            "appVersion": QtWidgets.QLabel(version),

            "apps": dock.SlimTableView(),
            "fullCommand": FullCommand(ctrl),

            # Error page
            "continue": QtWidgets.QPushButton("Continue"),
            "reset": QtWidgets.QPushButton("Reset"),

            "leftToggles": QtWidgets.QWidget(),
            "dockToggles": QtWidgets.QWidget(),

            "stateIndicator": StateIndicator(),
            "commandIndicator": CommandIndicator(),
        }

        # The order is reflected in the UI
        docks = odict((
            ("profiles", dock.Profiles(ctrl)),
            ("app", dock.App(ctrl)),
            ("packages", dock.Packages(ctrl)),
            ("context", dock.Context(ctrl)),
            ("environment", dock.Environment(ctrl)),
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
        layout.addWidget(widgets["noappsMessage"], 0)

        layout = QtWidgets.QVBoxLayout(pages["noprofiles"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(QtWidgets.QWidget(), 1)
        layout.addWidget(widgets["noprofileMessage"], 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(QtWidgets.QWidget(), 1)

        #  _______________________________________________________
        # |          |         |         |               |        |
        # |   logo   | profile |---------|               |--------|
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
                layout.setColumnStretch(addColumn.row, kwargs["stretch"])

        addColumn([widgets["leftToggles"]], 2, 1)
        addColumn([QtWidgets.QWidget()], stretch=2)
        addColumn([widgets["dockToggles"]], 2, 1)
        addColumn([QtWidgets.QWidget()], stretch=2)

        addColumn([QtWidgets.QLabel("allzpark"),
                   widgets["appVersion"]])
        addColumn([widgets["logo"]], 2, 1)

        _layouts = dict()
        _layouts["left"] = QtWidgets.QHBoxLayout(widgets["leftToggles"])
        _layouts["dock"] = QtWidgets.QHBoxLayout(widgets["dockToggles"])
        for _layout in _layouts.values():
            _layout.setContentsMargins(0, 0, 0, 0)
            _layout.setSpacing(0)

        for name, widget in docks.items():
            has_menu = hasattr(widget, "on_context_menu")
            BtnCls = (dock.PushButtonWithMenu
                      if has_menu else QtWidgets.QPushButton)
            toggle = BtnCls()
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

            if has_menu:
                toggle.customContextMenuRequested.connect(
                    widget.on_context_menu(self))

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

            _section = "left" if name == "profiles" else "dock"
            _layouts[_section].addWidget(toggle)

        layout = QtWidgets.QVBoxLayout(panels["body"])
        layout.setSpacing(0)
        layout.setContentsMargins(1, 0, 1, 0)
        layout.addWidget(widgets["apps"])
        layout.addWidget(widgets["fullCommand"])

        status_bar = self.statusBar()
        status_bar.addPermanentWidget(widgets["commandIndicator"])
        status_bar.addPermanentWidget(widgets["stateIndicator"])

        # Setup
        css = "QWidget { border-image: url(%s); }"
        widgets["logo"].setStyleSheet(css % res.find("Logo_64"))

        widgets["noappsMessage"].setReadOnly(True)
        widgets["noappsMessage"].setOpenExternalLinks(True)

        widgets["logo"].setCursor(QtCore.Qt.PointingHandCursor)
        widgets["logo"].setToolTip(allzparkconfig.help_url)

        docks["profiles"].set_model(ctrl.models["profiles"],
                                    ctrl.models["profileVersions"])
        docks["packages"].set_model(ctrl.models["packages"])
        docks["context"].set_model(ctrl.models["context"])
        docks["environment"].set_model(ctrl.models["environment"],
                                       ctrl.models["parentenv"],
                                       ctrl.models["diagnose"])
        docks["commands"].set_model(ctrl.models["commands"])

        proxy_model = model.ProxyModel(ctrl.models["apps"])
        widgets["apps"].setModel(proxy_model)

        widgets["errorMessage"].setAlignment(QtCore.Qt.AlignHCenter)

        widgets["logo"].clicked.connect(self.on_logo_clicked)

        docks["profiles"].profile_changed.connect(
            self.on_profilename_changed)
        docks["profiles"].profile_changed.connect(
            ctrl.models["profiles"].set_current)
        docks["profiles"].version_changed.connect(
            self.on_profileversion_changed)
        docks["profiles"].reset.connect(self.reset)

        widgets["reset"].clicked.connect(self.on_reset_clicked)
        widgets["continue"].clicked.connect(self.on_continue_clicked)
        widgets["apps"].activated.connect(self.on_app_clicked)
        widgets["apps"].customContextMenuRequested.connect(
            self.on_app_right_click)

        selection_model = widgets["apps"].selectionModel()
        selection_model.selectionChanged.connect(self.on_app_selection_changed)

        ctrl.models["apps"].modelReset.connect(self.on_apps_reset)
        ctrl.models["profiles"].modelReset.connect(
            self.on_profilename_reset)
        ctrl.models["profileVersions"].modelReset.connect(
            self.on_profileversion_reset)
        ctrl.resetted.connect(self.on_reset)
        ctrl.state_changed.connect(self.on_state_changed)
        ctrl.running_cmd_updated.connect(self.on_running_cmd_updated)
        ctrl.logged.connect(self.on_logged)
        ctrl.profile_changed.connect(self.on_profile_changed)
        ctrl.repository_changed.connect(self.on_repository_changed)
        ctrl.command_changed.connect(self.on_command_changed)
        ctrl.application_changed.connect(self.on_app_changed)

        self._pages = pages
        self._widgets = widgets
        self._panels = panels
        self._docks = docks
        self._ctrl = ctrl

        self.setup_docks()
        self.on_state_changed("booting")
        self.update_advanced_controls()
        self.setFocus()

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
        """Disables default popup for QDockWidget and QToolBar"""

    def update_advanced_controls(self):
        shown = bool(self._ctrl.state.retrieve("showAdvancedControls"))
        self._widgets["fullCommand"].setVisible(shown)

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

        docks = list(self._docks.values())

        area = QtCore.Qt.LeftDockWidgetArea
        profile = docks[0]
        self.addDockWidget(area, profile)

        area = QtCore.Qt.RightDockWidgetArea
        first = docks[1]
        self.addDockWidget(area, first)

        for widget in docks[2:]:
            if widget is first:
                continue

            self.addDockWidget(area, widget)
            self.tabifyDockWidget(first, widget)

    def reset(self):
        self._ctrl.reset()

    def on_reset(self):
        pass

    def on_command_changed(self, command):
        self._widgets["fullCommand"].setText(command)

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

        menu = dock.MenuWithTooltip(self)

        separator = QtWidgets.QWidgetAction(menu)
        separator.setDefaultWidget(QtWidgets.QLabel("Quick Launch"))
        menu.addAction(separator)

        def handle(action):
            tool = action.text()
            self._ctrl.launch(command=tool)

        for tool in tools:
            action = QtWidgets.QAction(tool, menu)
            action.triggered.connect(lambda _=False, a=action: handle(a))
            menu.addAction(action)

        menu.addSeparator()

        extras = (
            ["start cmd", "start powershell"]
            if os.name == "nt" else
            ["bash"]
        )

        for tool in extras:
            action = QtWidgets.QAction(tool, menu)
            action.triggered.connect(lambda _=False, a=action: handle(a))
            menu.addAction(action)

        menu.move(QtGui.QCursor.pos())
        menu.show()

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

        if key in ("showAllApps",
                   "showHiddenApps",
                   "patchWithFilter"):
            self._ctrl.reset()

        if key == "exclusionFilter":
            allzparkconfig.exclude_filter = value
            self._ctrl.reset()

        if key == "theme":
            user_css = self._ctrl.state.retrieve("userCss", "")
            self._originalcss = res.load_theme(value)
            self.setStyleSheet("\n".join([self._originalcss,
                                          res.format_stylesheet(user_css)]))

    def on_dock_toggled(self, dock, visible):
        """Make toggled dock the active dock"""

        if not visible:
            return

        # Handle the easy cases first
        app = QtWidgets.QApplication.instance()
        ctrl_held = app.keyboardModifiers() & QtCore.Qt.ControlModifier
        allow_multiple = bool(self._ctrl.state.retrieve("allowMultipleDocks"))

        if ctrl_held or not allow_multiple:
            ignore_allow_multiple = [
                # docks that are not restricted by this rule
                "profiles",
            ]

            for name, d in self._docks.items():
                if name in ignore_allow_multiple:
                    continue
                d.setVisible(d == dock)

            if len([d for d in self._docks.values() if d.isVisible()]) <= 1:
                # Only one or no visible dock
                return

        # Otherwise we'll want to make the newly visible dock the active tab.

        # Turns out to not be that easy
        # https://forum.qt.io/topic/42044/
        # tabbed-qdockwidgets-how-to-fetch-the-qwidgets-under-a-qtabbar/10

        # TabBar's are dynamically created as the user
        # moves docks around, and not all of them are
        # visible or in use at all times. (Poor garbage collection)
        bars = self.findChildren(QtWidgets.QTabBar, "")

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

    def on_profilename_clicked(self):
        pass

    def on_profilename_changed(self, profile):
        """User changed the profile"""
        self._ctrl.select_profile(profile)
        self._ctrl.state.store("startupProfile", profile)
        self.setFocus()

    def on_profileversion_changed(self, version):
        """User changed the profile version"""
        profile = self._ctrl.current_profile
        self._ctrl.select_profile(profile, version)
        self.setFocus()

    def on_logo_clicked(self):
        url = allzparkconfig.help_url
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def on_profile_changed(self, profile, version, refreshed=False):
        """Profile changed in the controller"""

        # Happens when editing requirements
        action = "Refreshing" if refreshed else "Changing"
        icon = res.find("Default_Profile")
        label = profile

        package = self._ctrl.state["rezProfiles"][profile][version]
        data = allzparkconfig.metadata_from_package(package)
        label = data["label"]

        # Facilitate overriding of icon via package metadata
        if data.get("icon"):
            try:
                values = {
                    "root": os.path.dirname(package.uri),
                    "width": px(32),
                    "height": px(32),
                }

                icon = data["icon"].format(**values).replace("\\", "/")

            except KeyError:
                self.tell("Misformatted %s.icon" % package.name)

            except TypeError:
                self.tell("Unsupported package repository "
                          "for icon of %s" % package.uri)

            except Exception:
                self.tell("Unexpected error coming from icon of %s"
                          % package.uri)

        self.tell("%s %s-%s" % (action, profile, version))
        self.setWindowTitle("%s  |  %s" % (label, self.title))

        profile_dock = self._docks["profiles"]
        profile_dock.update_current(profile, version, icon)

        toggle = profile_dock.toggle
        toggle.setIcon(res.icon(icon))

        # Determine aspect ratio
        height = px(32)
        pixmap = res.pixmap(icon)

        if pixmap.isNull():
            pixmap = res.pixmap("Default_Profile")

        pixmap = pixmap.scaledToHeight(height)
        width = pixmap.width()

        toggle.setIconSize(QtCore.QSize(width, height))
        toggle.setAutoFillBackground(True)

    def on_repository_changed(self):
        self.reset()

    def on_show_error(self):
        self._docks["console"].append(self._ctrl.current_error)
        self._docks["console"].raise_()

    def tell(self, message, level=logging.INFO):
        self._docks["console"].append(message, level)
        self.statusBar().showMessage(message, 2000)

    def on_logged(self, message, level):
        self._docks["console"].append(message, level)

    def on_running_cmd_updated(self, count):
        self._widgets["commandIndicator"].set_count(count)

    def on_state_changed(self, state):
        self.tell("State: %s" % state, logging.DEBUG)

        page = self._pages.get(str(state), self._pages["home"])
        page_name = page.objectName()
        self._panels["pages"].setCurrentWidget(page)

        launch_btn = self._docks["app"]._widgets["launchBtn"]
        launch_btn.setText("Launch")
        launch_btn.setEnabled(True)

        for widget in self._docks.values():
            widget.setEnabled(True)

        if page_name == "home":
            self._widgets["apps"].setEnabled(state == "ready")

        elif page_name == "noapps":
            message = self._ctrl.state["error"]
            self._widgets["noappsMessage"].setText(message)

        elif page_name == "noprofiles":
            pass

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

        self._widgets["stateIndicator"].set_status(str(state))
        self.update_advanced_controls()

    def on_launch_clicked(self):
        self._ctrl.launch()

    def on_profilename_reset(self):
        pass

    def on_profileversion_reset(self):
        pass

    def on_apps_reset(self):
        app = self._ctrl.state.retrieve("startupApplication")

        row = 0
        model = self._ctrl.models["apps"]

        if app:
            for row_ in range(model.rowCount()):
                index = model.index(row_, 0, QtCore.QModelIndex())
                name = model.data(index, "name")

                if app == name:
                    row = row_
                    self.tell("Using startup application %s" % name)
                    break

        self._widgets["apps"].selectRow(row)

    def on_app_clicked(self, index):
        """An app was double-clicked or Return was hit"""

        app = self._docks["app"]
        app.show()
        self.on_dock_toggled(app, visible=True)

    def on_app_selection_changed(self, selected, deselected):
        """The current app was changed

        Arguments:
            selected (QtCore.QItemSelection): ..
            deselected (QtCore.QItemSelection): ..

        """

        try:
            index = selected.indexes()[0]
        except IndexError:
            # No app was selected
            return

        model = index.model()
        app_request = model.data(index, "name")
        self._ctrl.select_application(app_request)

    def on_app_changed(self):
        selection_model = self._widgets["apps"].selectionModel()
        index = selection_model.selectedIndexes()[0]
        self._docks["app"].refresh(index)

    def showEvent(self, event):
        super(Window, self).showEvent(event)
        self._ctrl.state.store("default/geometry", self.saveGeometry())
        self._ctrl.state.store("default/windowState", self.saveState())

        if self._ctrl.state.retrieve("geometry"):
            self.tell("Restoring layout..", logging.DEBUG)
            self.restoreGeometry(self._ctrl.state.retrieve("geometry"))
            self.restoreState(self._ctrl.state.retrieve("windowState"))

    def closeEvent(self, event):
        self._ctrl.state.store("geometry", self.saveGeometry())
        self._ctrl.state.store("windowState", self.saveState())
        for timer in self._ctrl.timers.values():
            timer.stop()
        return super(Window, self).closeEvent(event)


class Indicator(QtWidgets.QWidget):
    """Status bar indicator base class"""

    def __init__(self, parent=None):
        super(Indicator, self).__init__(parent)
        widgets = {
            "icon": QtWidgets.QLabel(),
            "text": QtWidgets.QLabel(),
        }
        widgets["icon"].setObjectName("indicatorIcon")
        widgets["text"].setObjectName("indicatorText")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addWidget(widgets["icon"])
        layout.addWidget(widgets["text"])

        self._widgets = widgets
        self._size = QtCore.QSize(px(12), px(12))

    def setToolTip(self, tip):
        for widget in self._widgets.values():
            widget.setToolTip(tip)
        super(Indicator, self).setToolTip(tip)


class StateIndicator(Indicator):

    def __init__(self, parent=None):
        super(StateIndicator, self).__init__(parent)

        icons = {
            "busy": res.icon("chat-square-dots-fill").pixmap(self._size),
            "ready": res.icon("check-circle-fill").pixmap(self._size),
            "error": res.icon("exclamation-circle-fill").pixmap(self._size),
        }
        self._icons = icons

    def set_status(self, status):
        if status in ["errored", "noapps", "noprofiles", "pkgnotfound"]:
            key = "error"
        elif status == "ready":
            key = "ready"
        else:
            key = "busy"

        self._widgets["icon"].setPixmap(self._icons[key])
        self._widgets["text"].setText(status)
        self.setToolTip("Current status: %s" % status)


class CommandIndicator(Indicator):

    def __init__(self, parent=None):
        super(CommandIndicator, self).__init__(parent)
        icon = res.icon("gear-fill")
        self._widgets["icon"].setPixmap(icon.pixmap(self._size))

    def set_count(self, count):
        self._widgets["text"].setText(str(count))
        self.setToolTip("%d running commands" % count)


class FullCommand(QtWidgets.QWidget):
    def __init__(self, ctrl, parent=None):
        super(FullCommand, self).__init__(parent)

        widgets = {
            "options": QtWidgets.QComboBox(),
            "text": QtWidgets.QLineEdit(),
        }

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["options"])
        layout.addWidget(widgets["text"])

        up_icon = res.icon("Action_GoUp_3_Large_32.png")
        down_icon = res.icon("Action_GoDown_3_32.png")

        widgets["text"].setReadOnly(True)
        widgets["options"].addItem(up_icon, "Used Request")
        widgets["options"].addItem(down_icon, "Used Resolve")

        widgets["options"].currentIndexChanged.connect(self.on_option_changed)

        self._widgets = widgets
        self._ctrl = ctrl

        index = (
            0
            if ctrl.state.retrieve("serialisationMode") == "used_request"
            else 1
        )

        widgets["options"].setCurrentIndex(index)

    def setText(self, text):
        self._widgets["text"].setText(text)

    def on_option_changed(self, option):
        if option == 0:
            mode = "used_request"
            self._widgets["options"].setToolTip(
                "Used Request\n"
                "Use the final request made to Rez,\n"
                "excluding any indirect requirements."
            )
        else:
            mode = "used_resolve"
            self._widgets["options"].setToolTip(
                "Used Resolve\n"
                "Use the fully resolved list of packages,\n"
                "including packages that may not be suitable\n"
                "for another platform."
            )

        self._ctrl.update_command(mode)
