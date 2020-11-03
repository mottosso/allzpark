import os
import re
import time
import json
import logging
import collections
from itertools import chain

from .vendor.Qt import QtWidgets, QtCore, QtGui, QtCompat
from .vendor import qargparse, QtImageViewer

from . import resources as res, model, delegates, util
from . import _rezapi as rez
from . import allzparkconfig

try:
    from localz import lib as localz
except ImportError:
    localz = None

px = res.px


class AbstractDockWidget(QtWidgets.QDockWidget):
    """Default HTML <b>docs</b>"""

    icon = ""
    advanced = False

    message = QtCore.Signal(str)  # Handled by main window

    def __init__(self, title, parent=None):
        super(AbstractDockWidget, self).__init__(title, parent)
        self.layout().setContentsMargins(px(15), px(15), px(15), px(15))

        panels = {
            "help": QtWidgets.QLabel(),
            "body": QtWidgets.QStackedWidget(),
        }

        for name, widget in panels.items():
            widget.setAttribute(QtCore.Qt.WA_StyledBackground)
            widget.setObjectName("dock%s" % name.title())

        central = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
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
    """Aggregated information about the currently selected application"""

    icon = "Alert_Info_32"

    def __init__(self, ctrl, parent=None):
        super(App, self).__init__("App", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("App")

        default_app_icon = res.pixmap("Alert_Info_32")

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

        widgets["icon"].setPixmap(default_app_icon)
        widgets["environment"].setIcon(res.icon(Environment.icon))
        widgets["packages"].setIcon(res.icon(Packages.icon))
        widgets["terminal"].setIcon(res.icon(Console.icon))

        widgets["args"].changed.connect(self.on_arg_changed)

        widgets["launchBtn"].setCheckable(True)
        widgets["launchBtn"].clicked.connect(self.on_launch_clicked)

        proxy_model = model.ProxyModel(ctrl.models["commands"])
        widgets["commands"].setModel(proxy_model)

        self._ctrl = ctrl
        self._panels = panels
        self._widgets = widgets
        self._proxy = proxy_model
        self._default_app_icon = default_app_icon

        self.setWidget(panels["central"])

    def on_launch_clicked(self):
        self._ctrl.launch()

    def on_arg_changed(self, arg):
        if arg["name"] not in ("tool",):
            return

        ctrl = self._ctrl
        model = ctrl.models["apps"]
        app_name = ctrl.state["appRequest"]
        app_index = model.findIndex(app_name)
        value = arg.read()
        model.setData(app_index, value, arg["name"])

        if arg["name"] == "tool":
            ctrl.select_tool(value)

    def refresh(self, index):
        name = index.data(QtCore.Qt.DisplayRole)
        icon = index.data(QtCore.Qt.DecorationRole)

        if icon:
            icon = icon.pixmap(QtCore.QSize(px(32), px(32)))
            self._widgets["icon"].setPixmap(icon)
        else:
            self._widgets["icon"].setPixmap(self._default_app_icon)

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
            ("appRequest", name),
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
        widgets["text"].setObjectName("consolelog")

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["text"])

        self._widgets = widgets

    def append(self, line, level=logging.INFO):
        color = "<font color=\"%s\">" % res.log_level_color(level)

        line = line.replace(" ", "&nbsp;")
        line = line.replace("\n", "<br>")
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
            "central": QtWidgets.QTabWidget(),
        }

        pages = {
            "packages": QtWidgets.QWidget(),
        }

        args = [
            qargparse.Boolean(
                "useDevelopmentPackages",
                default=ctrl._state.retrieve("useDevelopmentPackages"),
                help="Include development packages in the resolve"),
            qargparse.String(
                "patch",
                default=ctrl._state.retrieve("patch"),
                help="Add packages to context"),
        ]

        if localz:
            args.insert(0, qargparse.Boolean(
                "useLocalizedPackages",
                default=ctrl._state.retrieve("useLocalizedPackages", True),
                help="Include localised packages in the resolve"),
            )

        widgets = {
            "args": qargparse.QArgumentParser(args),
            "view": SlimTableView(),
            "status": QtWidgets.QStatusBar(),
        }

        self.setWidget(panels["central"])

        panels["central"].addTab(pages["packages"], "Packages")

        layout = QtWidgets.QVBoxLayout(pages["packages"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(widgets["args"])
        layout.addWidget(widgets["view"], 1)
        layout.addWidget(widgets["status"])

        widgets["view"].setStretch(4)
        widgets["view"].setItemDelegate(delegates.Package(ctrl, self))
        widgets["view"].setEditTriggers(widgets["view"].DoubleClicked)
        widgets["view"].verticalHeader().setDefaultSectionSize(px(20))
        widgets["view"].customContextMenuRequested.connect(self.on_right_click)

        widgets["status"].setSizeGripEnabled(False)

        widgets["args"].changed.connect(self.on_argument_changed)
        ctrl.resetted.connect(self.on_resetted)

        self._ctrl = ctrl
        self._panels = panels
        self._pages = pages
        self._widgets = widgets

    def on_argument_changed(self, arg):
        if arg["name"] == "useDevelopmentPackages":
            self._ctrl._state.store("useDevelopmentPackages", arg.read())
            self._ctrl.reset()

        if arg["name"] == "useLocalizedPackages":
            self._ctrl._state.store("useLocalizedPackages", arg.read())
            self._ctrl.reset()

        if arg["name"] == "patch":
            self._ctrl._state.store("patch", arg.read())
            self._ctrl.reset()

    def on_resetted(self):
        patch = self._ctrl.state.retrieve("patch", "")
        arg = self._widgets["args"].find("patch")
        arg._write(patch)
        arg._previous = patch

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

        model_ = index.model()
        menu = MenuWithTooltip(self)
        edit = QtWidgets.QAction("Edit", menu)
        disable = QtWidgets.QAction("Disable", menu)
        default = QtWidgets.QAction("Set to default", menu)
        earliest = QtWidgets.QAction("Set to earliest", menu)
        latest = QtWidgets.QAction("Set to latest", menu)
        openfile = QtWidgets.QAction("Open file location", menu)
        copyfile = QtWidgets.QAction("Copy file location", menu)
        localize = QtWidgets.QAction("Localise selected...", menu)
        localize_related = QtWidgets.QAction("Localise related...", menu)
        localize_all = QtWidgets.QAction("Localise all...", menu)
        delocalize = QtWidgets.QAction("Delocalise selected...", menu)

        disable.setCheckable(True)
        disable.setChecked(model_.data(index, "disabled"))

        menu.addAction(edit)
        menu.addSeparator()
        menu.addAction(default)
        menu.addAction(earliest)
        menu.addAction(latest)
        menu.addSeparator()
        menu.addAction(openfile)
        menu.addAction(copyfile)

        if localz:
            enabled = True
            tooltip = None

            if index.data(model.LocalizingRole):
                enabled = False
                tooltip = "Localisation in progress..."

            elif model_.data(index, "state") in ("(dev)", "(localised)"):
                tooltip = "Package already local"
                enabled = False

            elif not model_.data(index, "relocatable"):
                tooltip = "Package does not support localisation"
                enabled = False

            menu.addSeparator()
            for action in (localize,
                           localize_related,
                           localize_all,
                           ):
                menu.addAction(action)
                action.setToolTip(tooltip or "")
                action.setEnabled(enabled)

            menu.addSeparator()
            menu.addAction(delocalize)
            delocalize.setEnabled(
                model_.data(index, "state") == "(localised)"
            )

            # Not yet implemented
            localize_all.setEnabled(False)
            localize_related.setEnabled(False)

        def on_edit():
            self._widgets["view"].edit(index)

        def on_default():
            package = model_.data(index, "package")
            self._ctrl.patch(package.name)
            self.message.emit("Package set to default")

        def on_earliest():
            versions = model_.data(index, "versions")
            earliest = versions[0]
            package = model_.data(index, "package")
            self._ctrl.patch("%s==%s" % (package.name, earliest))

            self.message.emit("Package set to earliest")

        def on_latest():
            versions = model_.data(index, "versions")
            latest = versions[-1]
            package = model_.data(index, "package")
            self._ctrl.patch("%s==%s" % (package.name, latest))

            self.message.emit("Package set to latest version")

        def on_openfile():
            package = model_.data(index, "package")
            pkg_uri = os.path.dirname(package.uri)
            fname = os.path.join(pkg_uri, "package.py")
            util.open_file_location(fname)
            self.message.emit("Opened %s" % fname)

        def on_copyfile():
            package = model_.data(index, "package")
            pkg_uri = os.path.dirname(package.uri)
            fname = os.path.join(pkg_uri, "package.py")
            clipboard = QtWidgets.QApplication.instance().clipboard()
            clipboard.setText(fname)
            self.message.emit("Copied %s" % fname)

        def on_disable():
            model_.setData(index, None, "override")
            model_.setData(index, disable.isChecked(), "disabled")
            self.message.emit("Package disabled")

        def on_localize():
            name = model_.data(index, "name")
            self._ctrl.localize(name)
            model_.setData(index, "(localising..)", "state")
            model_.setData(index, True, model.LocalizingRole)

        def on_delocalize():
            name = model_.data(index, "name")
            self._ctrl.delocalize(name)
            model_.setData(index, "(delocalising..)", "state")
            model_.setData(index, True, model.LocalizingRole)

        edit.triggered.connect(on_edit)
        disable.triggered.connect(on_disable)
        default.triggered.connect(on_default)
        earliest.triggered.connect(on_earliest)
        latest.triggered.connect(on_latest)
        openfile.triggered.connect(on_openfile)
        copyfile.triggered.connect(on_copyfile)
        localize.triggered.connect(on_localize)
        delocalize.triggered.connect(on_delocalize)

        menu.move(QtGui.QCursor.pos())
        menu.show()


class Context(AbstractDockWidget):
    """Full context relative the currently selected application"""

    icon = "App_Generic_4_32"
    advanced = True

    def __init__(self, ctrl, parent=None):
        super(Context, self).__init__("Context", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Context")

        panels = {
            "central": QtWidgets.QTabWidget(),
        }

        pages = {
            "context": QtWidgets.QWidget(),
            "graph": QtWidgets.QWidget(),
            "code": QtWidgets.QWidget(),
        }

        widgets = {
            "view": JsonView(),
            "graph": QtImageViewer.QtImageViewer(),
            "generateGraph": QtWidgets.QPushButton("Update"),
            "graphHotkeys": QtWidgets.QLabel(),
            "overlay": QtWidgets.QWidget(),
            "code": QtWidgets.QTextEdit(),
            "printCode": QtWidgets.QPushButton("Get Shell Code"),
        }

        # Expose to CSS
        for name, widget in chain(panels.items(),
                                  pages.items(),
                                  widgets.items()):
            widget.setAttribute(QtCore.Qt.WA_StyledBackground)
            widget.setObjectName(name)

        layout = QtWidgets.QVBoxLayout(pages["context"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["view"])

        layout = QtWidgets.QVBoxLayout(pages["graph"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["graph"], 1)

        layout = QtWidgets.QVBoxLayout(widgets["overlay"])
        layout.addWidget(widgets["graphHotkeys"])
        layout.addWidget(widgets["generateGraph"])
        layout.addWidget(QtWidgets.QWidget(), 1)

        layout = QtWidgets.QVBoxLayout(pages["code"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["code"])
        layout.addWidget(widgets["printCode"])

        panels["central"].addTab(pages["context"], "Context")
        panels["central"].addTab(pages["graph"], "Graph")
        panels["central"].addTab(pages["code"], "Code")

        ctrl.application_changed.connect(self.on_application_changed)

        widgets["view"].setSortingEnabled(True)
        widgets["view"].sortByColumn(0, QtCore.Qt.AscendingOrder)

        widgets["overlay"].setParent(pages["graph"])
        widgets["overlay"].show()

        widgets["code"].setObjectName("shellcode")
        widgets["code"].setReadOnly(True)

        widgets["generateGraph"].clicked.connect(self.on_generate_clicked)
        widgets["graphHotkeys"].setText("""\
            <font color=\"steelblue\"><b>Hotkeys</b></font>
            <br>
            <br>
            - <b>Pan</b>: Left mouse <br>
            - <b>Zoom</b>: Right mouse + drag <br>
            - <b>Reset</b>: Double-click right mouse <br>
        """)
        widgets["printCode"].clicked.connect(self.on_print_code_clicked)

        self._ctrl = ctrl
        self._panels = panels
        self._widgets = widgets
        self._model = None

        widgets["view"].setSortingEnabled(True)
        self.setWidget(panels["central"])

    def set_model(self, model_):
        proxy_model = QtCore.QSortFilterProxyModel()
        proxy_model.setSourceModel(model_)
        self._widgets["view"].setModel(proxy_model)
        self._model = model_

    def on_generate_clicked(self):
        pixmap = self._ctrl.graph()

        if not pixmap:
            self._widgets["graphHotkeys"].setText(
                "<b>GraphViz not found</b>"
                "<br>"
                "<br>"
                "This feature requires `dot` on PATH<br>"
                "See <a href=https://allzpark.com>allzpark.com</a> "
                "for details."
            )
            self._widgets["generateGraph"].hide()
            return

        self._widgets["graph"].setImage(pixmap)
        self._widgets["graph"]._pixmapHandle.setGraphicsEffect(None)

    def on_print_code_clicked(self):
        code = self._ctrl.shell_code()
        comment = "REM " if rez.system.shell == "cmd" else "# "

        pretty = []
        for ln in code.split("\n"):
            level = logging.DEBUG if ln.startswith(comment) else logging.INFO
            color = "<font color=\"%s\">" % res.log_level_color(level)
            pretty.append("%s%s</font>" % (color, ln.replace(" ", "&nbsp;")))

        self._widgets["code"].setText("<br>".join(pretty))

    def on_application_changed(self):
        self._widgets["code"].setPlainText("")
        if not self._widgets["graph"]._pixmapHandle:
            return

        grayscale = QtWidgets.QGraphicsColorizeEffect()
        grayscale.setColor(QtGui.QColor(0, 0, 0))
        self._widgets["graph"]._pixmapHandle.setGraphicsEffect(grayscale)


class Environment(AbstractDockWidget):
    """Full environment relative the currently selected application"""

    icon = "App_Heidi_32"
    advanced = True

    def __init__(self, ctrl, parent=None):
        super(Environment, self).__init__("Environment", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Environment")

        panels = {
            "central": QtWidgets.QTabWidget(),
        }

        pages = {
            "environment": QtWidgets.QWidget(),
            "editor": EnvironmentEditor(),
            "penv": QtWidgets.QWidget(),
            "diagnose": QtWidgets.QWidget(),
        }

        widgets = {
            "view": JsonView(),
            "penv": JsonView(),
            "test": JsonView(),
            "compute": QtWidgets.QPushButton("Compute Environment"),
        }

        layout = QtWidgets.QVBoxLayout(pages["environment"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["view"])

        layout = QtWidgets.QVBoxLayout(pages["penv"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["penv"])

        layout = QtWidgets.QVBoxLayout(pages["diagnose"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["test"])
        layout.addWidget(widgets["compute"])

        for view in ["view", "penv", "test"]:
            widgets[view].setSortingEnabled(True)
            widgets[view].sortByColumn(0, QtCore.Qt.AscendingOrder)

        pages["editor"].applied.connect(self.on_env_applied)

        panels["central"].addTab(pages["environment"], "Context")
        panels["central"].addTab(pages["penv"], "Parent")
        panels["central"].addTab(pages["editor"], "User")
        panels["central"].addTab(pages["diagnose"], "Diagnose")

        user_env = ctrl.state.retrieve("userEnv", {})
        pages["editor"].from_environment(user_env)
        pages["editor"].warning.connect(self.on_env_warning)
        widgets["compute"].clicked.connect(ctrl.test_environment)

        self.setWidget(panels["central"])

        self._ctrl = ctrl
        self._panels = panels
        self._pages = pages
        self._widgets = widgets

    def set_model(self, environ, parent, diagnose):
        proxy_model = QtCore.QSortFilterProxyModel()
        proxy_model.setSourceModel(environ)
        self._widgets["view"].setModel(proxy_model)

        proxy_model = QtCore.QSortFilterProxyModel()
        proxy_model.setSourceModel(parent)
        self._widgets["penv"].setModel(proxy_model)

        proxy_model = QtCore.QSortFilterProxyModel()
        proxy_model.setSourceModel(diagnose)
        self._widgets["test"].setModel(proxy_model)

    def on_env_applied(self, env):
        self._ctrl.state.store("userEnv", env)
        self._ctrl.info("User environment successfully saved")

    def on_env_warning(self, message):
        self._ctrl.warning(message)


class JsonView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(JsonView, self).__init__(parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_right_click)

    def on_right_click(self, position):
        index = self.indexAt(position)

        if not index.isValid():
            # Clicked outside any item
            return

        model_ = index.model()
        menu = MenuWithTooltip(self)
        copy = QtWidgets.QAction("Copy JSON", menu)
        copy_full = QtWidgets.QAction("Copy full JSON", menu)

        menu.addAction(copy)
        menu.addAction(copy_full)
        menu.addSeparator()

        def on_copy():
            text = str(model_.data(index, model.JsonModel.JsonRole))
            app = QtWidgets.QApplication.instance()
            app.clipboard().setText(text)

        def on_copy_full():
            if isinstance(model_, QtCore.QSortFilterProxyModel):
                data = model_.sourceModel().json()
            else:
                data = model_.json()

            text = json.dumps(data,
                              indent=4,
                              sort_keys=True,
                              ensure_ascii=False)

            app = QtWidgets.QApplication.instance()
            app.clipboard().setText(text)

        copy.triggered.connect(on_copy)
        copy_full.triggered.connect(on_copy_full)

        menu.move(QtGui.QCursor.pos())
        menu.show()


class TextEditWithFocus(QtWidgets.QTextEdit):
    focusLost = QtCore.Signal()

    def focusOutEvent(self, event):
        super(TextEditWithFocus, self).focusOutEvent(event)
        self.focusLost.emit()


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

        widgets["view"].setSortingEnabled(True)
        widgets["view"].customContextMenuRequested.connect(self.on_right_click)

        self._panels = panels
        self._widgets = widgets

        self.setWidget(panels["central"])

    def set_model(self, model_):
        proxy_model = model.ProxyModel(model_)
        self._widgets["view"].setModel(proxy_model)

    def on_right_click(self, position):
        view = self._widgets["view"]
        index = view.indexAt(position)

        if not index.isValid():
            # Clicked outside any item
            return

        model = index.model()

        menu = QtWidgets.QMenu(self)
        copy_pid = QtWidgets.QAction("Copy pid", menu)

        def on_copy_pid():
            clipboard = QtWidgets.QApplication.instance().clipboard()
            command = model.data(index, "object")
            pid = str(command.pid)
            clipboard.setText(pid)
            self.message.emit("Copying %s" % pid)

        if model.data(index, "running") != "killed":
            copy_pid.triggered.connect(on_copy_pid)
        else:
            copy_pid.setEnabled(False)

        # See https://github.com/mottosso/allzpark/issues/88
        # menu.addAction(copy_pid)

        menu.move(QtGui.QCursor.pos())
        menu.show()


class EnvironmentEditor(QtWidgets.QWidget):
    applied = QtCore.Signal(dict)  # environment
    warning = QtCore.Signal(str)  # message

    def __init__(self, parent=None):
        super(EnvironmentEditor, self).__init__(parent)

        widgets = {
            "textEdit": TextEditWithFocus(),
        }

        font = self.font()
        font.setFamily("Courier")
        font.setFixedPitch(True)
        font.setPointSize(10)

        widgets["textEdit"].setFont(font)
        widgets["textEdit"].setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(px(2))
        layout.addWidget(widgets["textEdit"])

        self._widgets = widgets
        self._edited = False

        widgets["textEdit"].focusLost.connect(self.on_focus_lost)
        widgets["textEdit"].textChanged.connect(self.on_text_changed)
        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.on_apply_clicked)

    def on_apply_clicked(self):
        if not self._edited:
            self.warning.emit("Already saved")
            return

        self.on_focus_lost()

    def from_environment(self, environ):
        if not environ:
            return

        text = "\n".join([
            "%s=%s" % (key, value)
            for key, value in environ.items()
        ])

        self._widgets["textEdit"].setPlainText(text)

    def to_environment(self):
        """Serialise text to dictionary"""

        # Maintain order as written
        env = collections.OrderedDict()

        textedit = self._widgets["textEdit"]
        for line in textedit.toPlainText().splitlines():
            if line.startswith("#"):
                continue

            try:
                key, value = line.split("=")
            except Exception:
                continue

            key = key.rstrip(" ")  # Tailing space
            value = value.strip(" ")  # Leading space

            # Validate key
            validator = re.compile(r'^[A-Za-z0-9\._]+$')
            if not validator.match(key):
                self.warning.emit("Invalid key: %s" % key)
                continue

            env[key] = value
        return env

    def on_focus_lost(self):
        if not self._edited:
            return

        env = self.to_environment()
        self.applied.emit(env)
        self._edited = False

    def on_text_changed(self):
        # Prevent focus from triggering serialisation,
        # if it had already been serialised with Ctrl+S
        self._edited = True


class CssEditor(QtWidgets.QWidget):
    applied = QtCore.Signal(str)  # css

    def __init__(self, parent=None):
        super(CssEditor, self).__init__(parent)

        widgets = {
            "textEdit": QtWidgets.QTextEdit(),
            "apply": QtWidgets.QPushButton("Apply"),
        }

        # Cannot set via CSS, as we need to query the
        # size of it in order to get the tab width below..
        font = self.font()
        font.setFamily("Courier")
        font.setFixedPitch(True)
        font.setPointSize(10)

        widgets["textEdit"].setFont(font)
        widgets["textEdit"].setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(px(2))
        layout.addWidget(widgets["textEdit"])
        layout.addWidget(widgets["apply"])

        widgets["apply"].clicked.connect(self.on_apply_clicked)

        try:
            width = 2 * widgets["textEdit"].fontMetrics().width(" ")
            widgets["textEdit"].setTabStopWidth(width)
        except AttributeError:
            # Qt 5+ only
            pass

        self._widgets = widgets
        self._highlighter = CssHighlighter(widgets["textEdit"].document())

        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.on_apply_clicked)

    def on_apply_clicked(self):
        textedit = self._widgets["textEdit"]
        self.applied.emit(textedit.toPlainText())


class Preferences(AbstractDockWidget):
    """Preferred settings relative the current user"""

    icon = "Action_GoHome_32"

    options = [
        qargparse.Info("startupProfile", help=(
            "Load this profile on startup"
        )),
        qargparse.Info("startupApplication", help=(
            "Load this application on startup"
        )),

        qargparse.Separator("Appearance"),

        qargparse.Enum("theme", items=res.theme_names(), help=(
            "GUI skin. May need to restart Allzpark after changed."
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
            "List everything from allzparkconfig:applications\n"
            "not just the ones specified for a given profile."
        )),
        qargparse.Boolean("showHiddenApps", help=(
            "Show apps with metadata['hidden'] = True"
        )),

        qargparse.Boolean("patchWithFilter", help=(
            "Use the current exclusion filter when patching.\n"
            "This enables patching of packages outside of a filter, \n"
            "such as *.beta packages, with every other package still \n"
            "qualifying for that filter."
        )),
        qargparse.Integer("clearCacheTimeout", min=1, default=10, help=(
            "Clear package repository cache at this interval, in seconds. \n\n"

            "Default 10. (Requires restart)\n\n"

            "Normally, filesystem calls like `os.listdir` are cached \n"
            "so as to avoid unnecessary calls. However, whenever a new \n"
            "version of a package is released, it will remain invisible \n"
            "until this cache is cleared. \n\n"

            "Clearing ths cache should have a very small impact on \n"
            "performance and is safe to do frequently. It has no effect \n"
            "on memcached which has a much greater impact on performanc."
        )),

        qargparse.String(
            "exclusionFilter",
            default=allzparkconfig.exclude_filter,
            help="Exclude versions that match this expression"),

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
            "central": QtWidgets.QTabWidget(),
        }

        pages = {
            "settings": QtWidgets.QWidget(),
            "cssEditor": CssEditor(),
        }

        widgets = {
            "options": qargparse.QArgumentParser(
                self.options, storage=ctrl._storage)
        }

        layout = QtWidgets.QVBoxLayout(pages["settings"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["options"])

        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(pages["settings"])
        scroll.setWidgetResizable(True)

        widgets["options"].changed.connect(self.handler)
        pages["cssEditor"].applied.connect(self.on_css_applied)

        panels["central"].addTab(scroll, "Settings")
        panels["central"].addTab(pages["cssEditor"], "CSS")

        self._panels = panels
        self._pages = pages
        self._widgets = widgets
        self._ctrl = ctrl
        self._window = window

        user_css = ctrl.state.retrieve("userCss", "")
        pages["cssEditor"]._widgets["textEdit"].setPlainText(user_css)

        self.setWidget(panels["central"])

    def handler(self, argument):
        self._window.on_setting_changed(argument)

    def on_css_applied(self, css):
        self._ctrl.state.store("userCss", css)
        self._window.setStyleSheet("\n".join([
            self._window._originalcss, res.format_stylesheet(css)]))
        self._window.tell("Applying css..")


class SlimTableView(QtWidgets.QTableView):
    doSort = QtCore.Signal(int, QtCore.Qt.SortOrder)

    def __init__(self, parent=None):
        super(SlimTableView, self).__init__(parent)
        self.setShowGrid(False)
        self.verticalHeader().hide()
        self.setSelectionMode(self.SingleSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)
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


class PushButtonWithMenu(QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
        super(PushButtonWithMenu, self).__init__(*args, **kwargs)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def mousePressEvent(self, event):
        """Do request a context menu, but on mouse *press*, not release"""

        # Important, call this first to have the item be selected,
        # as per default, and *then* ask for a context menu. That
        # way, the menu and selection aligns.
        try:
            return super(PushButtonWithMenu, self).mousePressEvent(event)

        finally:
            if event.button() == QtCore.Qt.RightButton:
                self.customContextMenuRequested.emit(event.pos())


class LineEditWithCompleter(QtWidgets.QLineEdit):
    changed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(LineEditWithCompleter, self).__init__(parent)

        proxy = QtCore.QSortFilterProxyModel(self)
        proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        completer = QtWidgets.QCompleter(proxy, self)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setCompletionMode(completer.UnfilteredPopupCompletion)
        completer.setMaxVisibleItems(15)

        self.setCompleter(completer)
        self.editingFinished.connect(self.onEditingFinished)

        self._completer = completer
        self._focused = False
        self._proxy = proxy
        self._current = None

    def setModel(self, model):
        self._proxy.setSourceModel(model)
        self._completer.setModel(self._proxy)

    def setText(self, text):

        # Keep track of a "default" such that we can revert back to
        # it following a bad completion.
        self._current = text

        return super(LineEditWithCompleter, self).setText(text)

    def resetText(self):
        self.setText(self._current)

    def mousePressEvent(self, event):
        super(LineEditWithCompleter, self).mousePressEvent(event)

        # Automatically show dropdown on select
        self._completer.complete()
        self.selectAll()

    def onEditingFinished(self):
        # For whatever reason, the completion prefix isn't updated
        # when coming from the user selecting an item from the
        # completion listview. (Windows 10, PySide2, Python 3.7)
        self._completer.setCompletionPrefix(self.text())

        suggested = self._completer.currentCompletion()

        if not suggested:
            return self.resetText()

        self.changed.emit(suggested)


class MenuWithTooltip(QtWidgets.QMenu):
    """QMenu typically doesn't draw tooltips"""

    def event(self, event):
        if event.type() == QtCore.QEvent.ToolTip and self.activeAction() != 0:

            try:
                tooltip = self.activeAction().toolTip()
            except AttributeError:
                # Can sometimes return None
                pass
            else:
                QtWidgets.QToolTip.showText(
                    event.globalPos(),
                    tooltip
                )

        # Account for QStatusBar queries about tooltip
        # These typically are only available on hovering
        # an action for some time, which isn't reflected
        # in querying the menu itself for a tooltip.
        elif event.type() == QtCore.QEvent.MouseMove:
            try:
                tooltip = self.activeAction().toolTip()

                # Some tooltips are multi-line, and the statusbar
                # typically ignores newlines and writes it all out
                # as one long line.
                tooltip = tooltip.splitlines()[0]

                self.setToolTip(tooltip)

            except (AttributeError, IndexError):
                pass

            QtWidgets.QToolTip.hideText()

        return super(MenuWithTooltip, self).event(event)


class CssHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(CssHighlighter, self).__init__(parent)

        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground(QtCore.Qt.darkBlue)
        keyword_format.setFontWeight(QtGui.QFont.Bold)

        keywordPatterns = [
            "\\bchar\\b", "\\bclass\\b", "\\bconst\\b",
            "\\bdouble\\b", "\\benum\\b", "\\bexplicit\\b", "\\bfriend\\b",
            "\\binline\\b", "\\bint\\b", "\\blong\\b", "\\bnamespace\\b",
            "\\boperator\\b", "\\bprivate\\b", "\\bprotected\\b",
            "\\bpublic\\b", "\\bshort\\b", "\\bsignals\\b", "\\bsigned\\b",
            "\\bslots\\b", "\\bstatic\\b", "\\bstruct\\b",
            "\\btemplate\\b", "\\btypedef\\b", "\\btypename\\b",
            "\\bunion\\b", "\\bunsigned\\b", "\\bvirtual\\b", "\\bvoid\\b",
            "\\bvolatile\\b"
        ]

        self.rules = [
            (QtCore.QRegExp(pattern), keyword_format)
            for pattern in keywordPatterns
        ]

        class_format = QtGui.QTextCharFormat()
        class_format.setFontWeight(QtGui.QFont.Bold)
        class_format.setForeground(QtCore.Qt.darkMagenta)
        self.rules.append((
            QtCore.QRegExp("\\bQ[A-Za-z]+\\b"),
            class_format
        ))

        id_format = QtGui.QTextCharFormat()
        id_format.setFontWeight(QtGui.QFont.Bold)
        id_format.setForeground(QtCore.Qt.darkBlue)
        self.rules.append((
            QtCore.QRegExp(r"#\w{1,}\b"),
            id_format
        ))

        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(QtCore.Qt.red)
        self.rules.append((
            QtCore.QRegExp("//[^\n]*"),
            comment_format
        ))

        self.multicomment_format = QtGui.QTextCharFormat()
        self.multicomment_format.setForeground(QtCore.Qt.gray)

        quote_format = QtGui.QTextCharFormat()
        quote_format.setForeground(QtCore.Qt.darkGreen)
        self.rules.append(
            (QtCore.QRegExp("\".*\""), quote_format)
        )

        function_format = QtGui.QTextCharFormat()
        function_format.setFontItalic(True)
        function_format.setForeground(QtCore.Qt.blue)
        self.rules.append((
            QtCore.QRegExp("\\b[A-Za-z0-9_]+(?=\\()"),
            function_format
        ))

        self.comment_start_exp = QtCore.QRegExp("/\\*")
        self.comment_end_exp = QtCore.QRegExp("\\*/")

    def highlightBlock(self, text):
        for pattern, format in self.rules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.comment_start_exp.indexIn(text)

        while startIndex >= 0:
            endIndex = self.comment_end_exp.indexIn(text, startIndex)

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = (
                    endIndex -
                    startIndex +
                    self.comment_end_exp.matchedLength()
                )

            self.setFormat(
                startIndex,
                commentLength,
                self.multicomment_format
            )
            startIndex = self.comment_start_exp.indexIn(
                text, startIndex + commentLength)


class ProfileView(QtWidgets.QTreeView):

    activated = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(ProfileView, self).__init__(parent)

        self.setHeaderHidden(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, position):
        index = self.indexAt(position)

        if not index.isValid():
            # Clicked outside any item
            return

        model_ = index.model()
        menu = QtWidgets.QMenu(self)

        name = str(model_.data(index, model.NameRole))

        activate = QtWidgets.QAction("Activate", menu)
        activate.triggered.connect(lambda: self.on_activate(name))
        menu.addAction(activate)

        menu.move(QtGui.QCursor.pos())
        menu.show()

    def on_activate(self, profile):
        self.activated.emit(profile)

    def selected_index(self):
        return self.selectionModel().currentIndex()

    def selected_profile(self):
        index = self.selected_index()
        if index.isValid():
            return index.data(model.NameRole)


class Profiles(AbstractDockWidget):
    """Listing and changing profiles"""

    icon = "Default_Profile"

    profile_changed = QtCore.Signal(str)
    version_changed = QtCore.Signal(str)
    reset = QtCore.Signal()

    def __init__(self, ctrl, parent=None):
        super(Profiles, self).__init__("Profiles", parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setObjectName("Profiles")

        panels = {
            "central": QtWidgets.QWidget(),
            "head": QtWidgets.QWidget(),
            "body": QtWidgets.QWidget(),
        }

        widgets = {
            # head: current profile
            "icon": QtWidgets.QLabel(),
            "name": QtWidgets.QLabel(),
            "version": LineEditWithCompleter(),

            # body: profiles view and toolset
            "refresh": QtWidgets.QPushButton(""),
            "search": QtWidgets.QLineEdit(),
            "view": ProfileView(),

            "tools": QtWidgets.QWidget(),
            "favorite": QtWidgets.QPushButton(""),
            "filtering": QtWidgets.QPushButton(""),
            "expand": QtWidgets.QPushButton(""),
            "collapse": QtWidgets.QPushButton(""),
            "sep1": QtWidgets.QFrame(),
            "versioning": QtWidgets.QPushButton(""),
        }

        models = {
            "source": None,
            "proxy": model.ProfileProxyModel(),
        }

        layout = QtWidgets.QGridLayout(panels["head"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["icon"], 0, 0, 2, 1)
        layout.addWidget(widgets["name"], 0, 1)
        layout.addWidget(widgets["version"], 1, 1)

        layout = QtWidgets.QVBoxLayout(widgets["tools"])
        layout.setContentsMargins(0, 2, 0, 0)
        layout.addWidget(widgets["favorite"])
        layout.addWidget(widgets["filtering"])
        layout.addWidget(widgets["expand"])
        layout.addWidget(widgets["collapse"])
        layout.addWidget(widgets["sep1"])
        layout.addWidget(widgets["versioning"])
        # (epic) quick make profile
        # (epic) quick edit profile
        # (epic) remove or hide local profile
        layout.addStretch()

        layout = QtWidgets.QGridLayout(panels["body"])
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widgets["refresh"], 0, 0)
        layout.addWidget(widgets["tools"], 1, 0)
        layout.addWidget(widgets["search"], 0, 1)
        layout.addWidget(widgets["view"], 1, 1)

        layout = QtWidgets.QVBoxLayout(panels["central"])
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(panels["head"])
        layout.addWidget(panels["body"], stretch=True)

        version = widgets["version"]
        search = widgets["search"]
        view = widgets["view"]
        proxy = models["proxy"]

        view.setModel(proxy)
        selection = view.selectionModel()

        proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        search.setPlaceholderText("Filter profiles..")

        version.setToolTip("Click to change profile version")
        version.setEnabled(False)

        widgets["sep1"].setFrameStyle(QtWidgets.QFrame.HLine
                                      | QtWidgets.QFrame.Plain)

        # icons
        icon_size = QtCore.QSize(14, 14)

        icon = res.icon("refresh")
        widgets["refresh"].setIcon(icon)
        widgets["refresh"].setIconSize(icon_size)

        icon = res.icon("star_bright")
        icon.addPixmap(res.pixmap("star_dim"), icon.Disabled)
        widgets["favorite"].setIcon(icon)
        widgets["favorite"].setIconSize(icon_size)

        icon = QtGui.QIcon()
        icon.addPixmap(res.pixmap("filter_on"), icon.Normal, icon.On)
        icon.addPixmap(res.pixmap("filter_off"), icon.Normal, icon.Off)
        widgets["filtering"].setIcon(icon)
        widgets["filtering"].setIconSize(icon_size)
        widgets["filtering"].setCheckable(True)
        widgets["filtering"].setAutoRepeat(True)

        icon = QtGui.QIcon()
        icon.addPixmap(res.pixmap("version_on"), icon.Normal, icon.On)
        icon.addPixmap(res.pixmap("version_off"), icon.Normal, icon.Off)
        widgets["versioning"].setIcon(icon)
        widgets["versioning"].setIconSize(icon_size)
        widgets["versioning"].setCheckable(True)
        widgets["versioning"].setAutoRepeat(True)

        icon = res.icon("expand")
        widgets["expand"].setIcon(icon)
        widgets["expand"].setIconSize(icon_size)

        icon = res.icon("collapse")
        widgets["collapse"].setIcon(icon)
        widgets["collapse"].setIconSize(icon_size)

        icon = res.icon("Default_Profile")
        icon = icon.pixmap(QtCore.QSize(px(32), px(32)))
        widgets["icon"].setPixmap(icon)

        # signals
        view.activated.connect(self.profile_changed.emit)
        selection.currentChanged.connect(self.on_selected_profile_changed)
        version.changed.connect(self.version_changed.emit)
        search.textChanged.connect(view.expandAll)
        search.textChanged.connect(proxy.setFilterFixedString)
        widgets["refresh"].clicked.connect(self.reset.emit)
        widgets["favorite"].clicked.connect(self.on_favorite)
        widgets["filtering"].clicked.connect(self.on_filtering)
        widgets["versioning"].clicked.connect(
            lambda *args: version.setEnabled(not version.isEnabled()))
        widgets["expand"].clicked.connect(view.expandAll)
        widgets["collapse"].clicked.connect(view.collapseAll)
        ctrl.resetted.connect(view.expandAll)

        self._widgets = widgets
        self._models = models
        self._ctrl = ctrl

        self.setWidget(panels["central"])

        self.update_favorite_btn(None)  # nothing selected on startup

    def set_model(self, profile_model, version_model):
        # profile
        proxy = self._models["proxy"]
        proxy.setSourceModel(profile_model)
        self._models["source"] = profile_model
        self._widgets["filtering"].setChecked(profile_model.is_filtering)
        # version
        self._widgets["version"].setModel(version_model)

    def on_context_menu(self, window):
        def _on_context_menu(*args):
            name = self._models["source"].current

            menu = MenuWithTooltip(window)
            separator = QtWidgets.QWidgetAction(menu)
            separator.setDefaultWidget(QtWidgets.QLabel(name))
            menu.addAction(separator)

            def on_reset():
                window.reset()

            reset = QtWidgets.QAction("Reset", menu)
            reset.triggered.connect(on_reset)
            reset.setToolTip("Re-scan repository for new Rez packages")
            menu.addAction(reset)

            menu.addSeparator()

            menu.move(QtGui.QCursor.pos())
            menu.show()

        return _on_context_menu

    def on_favorite(self):
        model_ = self._models["source"]
        proxy = self._models["proxy"]
        view = self._widgets["view"]
        index = proxy.mapToSource(view.selected_index())

        model_.update_favorite(self._ctrl, index)
        model_.update_profile_icon(index)

    def on_filtering(self):
        proxy = self._models["proxy"]
        model_ = self._models["source"]
        model_.is_filtering = not model_.is_filtering

        proxy.invalidateFilter()

    def on_selected_profile_changed(self):
        view = self._widgets["view"]
        self.update_favorite_btn(view.selected_profile())

    def update_favorite_btn(self, profile):
        btn = self._widgets["favorite"]
        btn.setEnabled(bool(profile))

    def update_current(self, profile, version, icon):
        self._widgets["name"].setText(profile)
        self._widgets["version"].setText(version)

        icon = res.icon(icon)
        icon = icon.pixmap(QtCore.QSize(px(32), px(32)))
        self._widgets["icon"].setPixmap(icon)
