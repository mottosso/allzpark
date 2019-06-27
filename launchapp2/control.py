"""Orchestrates view.py and model.py"""

import os
import time
import logging
import threading
import traceback
import subprocess

from collections import OrderedDict as odict

from .vendor.Qt import QtCore
from .vendor import transitions
from . import model, util

# Third-party dependencies
from rez.packages_ import iter_packages
from rez.resolved_context import ResolvedContext
import rez.exceptions
import rez.package_filter

log = logging.getLogger(__name__)

LAUNCHAPP_APPS = os.getenv("LAUNCHAPP_APPS")
LAUNCHAPP_PROJECTS = os.getenv("LAUNCHAPP_PROJECTS")

# Backwards compatibility
LAUNCHAPP_PROJECTS = LAUNCHAPP_PROJECTS or os.getenv("LAUNCHAPP_ROOT")


class State(dict):
    """Transient, persistent and machine for state

    The state is used to keep track of which applications
    is the "current" one, along with managing the current
    "state" such as whether the application is busy loading,
    whether it's ready for user input. It also manages persistent
    data, the kind that is stored until the next time the
    application is launched.

    """

    def __init__(self, ctrl, storage):
        super(State, self).__init__({
            "projectName": storage.value("startupProject"),
            "projectVersion": None,
            "appName": storage.value("startupApplication"),
            "appVersion": None,

            # Current error, if any
            "error": None,

            # Currently commands applications
            "commands": [],

            # Previously loaded project Rez packages
            "rezProjects": {},

            # Currently loaded Rez contexts
            "rezContexts": {},
            "rezApps": odict(),
        })

        self._ctrl = ctrl
        self._storage = storage

    def store(self, key, value):
        """Write to persistent storage

        Arguments:
            key (str): Name of variable
            value (object): Any datatype

        """

        self._storage.setValue(key, value)

    def retrieve(self, key):
        """Read from persistent storage

        Arguments:
            key (str): Name of variable

        """

        value = self._storage.value(key)

        # Account for poor serialisation format
        # TODO: Implement a better format
        true = ["2", "1", "true", True, 1, 2]
        false = ["0", "false", False, 0]

        if value in true:
            value = True

        if value in false:
            value = False

        return value

    def on_enter_booting(self):
        self._ctrl.info("Booting..")

    def on_enter_selectproject(self):
        pass

    def on_enter_resolving(self):
        pass

    def on_enter_launching(self):
        self._ctrl.info("Application is being launched..")
        util.delay(self.to_ready, 500)

    def on_enter_noapps(self):
        project = self["projectName"]
        self._ctrl.info("No applications were found for %s" % project)

    def on_enter_loading(self):
        self._ctrl.info("Loading..")

    def on_enter_ready(self):
        self._ctrl.info("Ready")


class _State(transitions.State):
    def __init__(self, *args, **kwargs):
        help = kwargs.pop("help", "")
        super(_State, self).__init__(*args, **kwargs)
        self.help = help

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.name == other.name
        return self.name == other

    def __ne__(self, other):
        return not self.__eq__(other)


class Controller(QtCore.QObject):
    state_changed = QtCore.Signal(_State)
    logged = QtCore.Signal(str, int)  # message, level
    project_changed = QtCore.Signal(str, str)  # before, after

    states = [
        _State("booting", help="launchapp is booting, hold on"),
        _State("resolving", help="Rez is busy resolving a context"),
        _State("loading", help="Something is taking a moment"),
        _State("errored", help="Something has gone wrong"),
        _State("launching", help="An application is launching"),
        _State("ready", help="Awaiting user input"),
        _State("noproject", help="A given project package was not found"),
        _State("noapps", help="There were no applications to choose from"),
        _State("notresolved", help="Rez couldn't resolve a request"),
        _State("pkgnotfound", help="One or more packages was not found"),
    ]

    def __init__(self, storage, parent=None):
        super(Controller, self).__init__(parent)

        state = State(self, storage)

        models = {
            "projectVersions": QtCore.QStringListModel(),
            "apps": model.ApplicationModel(),

            # Docks
            "packages": model.PackagesModel(),
            "context": model.JsonModel(),
            "environment": model.EnvironmentModel(),
            "commands": model.CommandsModel(),
        }

        timers = {
            "commandsPoller": QtCore.QTimer(self),
        }

        timers["commandsPoller"].timeout.connect(self.on_tasks_polled)
        timers["commandsPoller"].start(500)

        # Initialize the state machine
        self._machine = transitions.Machine(
            model=state,
            states=self.states,
            initial="booting",
            after_state_change=[self.on_state_changed],

            # Add "on_enter_<state name>" to model
            auto_transitions=True,
        )

        self._models = models
        self._storage = storage
        self._state = state
        self._name_to_state = {
            state.name: state
            for state in self.states
        }

        state.on_enter_booting()

    # ----------------
    # Data
    # ----------------

    @property
    def models(self):
        return self._models

    @property
    def state(self):
        return self._state

    @property
    def current_error(self):
        return self._state["error"]

    @property
    def current_project(self):
        return self._state["projectName"]

    @property
    def current_application(self):
        return self._state["appName"]

    @property
    def current_tool(self):
        return self._state["tool"]

    def context(self, app_name):
        return self._state["rezContexts"][app_name].to_dict()

    def environ(self, app_name):
        return self._state["rezContexts"][app_name].get_environ()

    def resolved_packages(self, app_name):
        return self._state["rezContexts"][app_name].resolved_packages

    def find(self, package_name, callback=lambda result: None):
        return util.defer(
            iter_packages, args=[package_name],
            on_success=callback
        )

    # ----------------
    # Events
    # ----------------

    def on_tasks_polled(self):
        self._models["commands"].poll()

    def on_state_changed(self):
        state = self._name_to_state[self._state.state]
        self.state_changed.emit(state)

    def on_unhandled_exception(self, type, value, tb):
        """From sys.excepthook

        Exceptions are normally handled close to the caller,
        but some exceptions are better handled globally. For
        example, if a PackageCommandError occurs, there is
        little a caller can do. The problem must be addressed
        by the user, outside of the entire program, so best we
        can do is let them know as nicely as possible.

        Arguments:
            type (Exception): Subclass of Exception
            value (str): Message to the user
            tb (str): Full traceback

        Returns:
            handled (bool): True is the application dealt
                with it, False otherwise. An unhandled exception
                is raised to the command-line/caller.

        """

        RexUndefinedVariableError = rez.exceptions.RexUndefinedVariableError

        if rez.exceptions.RexError is type:
            # These are re-raised as a more specific
            # exception, e.g. RexUndefinedVariableError
            pass

        if RexUndefinedVariableError is type:
            pass

        if rez.exceptions.PackageCommandError is type:
            pass

        self.error("".join(traceback.format_tb(tb)))
        self.error(str(value))
        self._state.to_errored()

    # ----------------
    # Methods
    # ----------------

    @util.async_
    def reset(self, root=None, on_success=lambda: None):
        """Initialise controller with `root`

        Projects are listed at `root` and matched
        with its corresponding Rez package.

        Arguments:
            root (str): Absolute path to projects on disk

        """

        self.info("Resetting..")
        root = root or self._state["root"]
        assert root, "Tried resetting without a root, this is a bug"

        def do():
            # On resetting after startup, there will be a
            # currently selected project that may differ from
            # the startup project.
            current_project = self._state["projectName"]

            # Find last used project from user preferences
            if not current_project:
                current_project = self._state.retrieve("startupProject")

            # The user has never opened the GUI before,
            # or user preferences has been wiped.
            if not current_project:
                try:
                    projects = self.list_projects(root)
                    current_project = projects[-1]

                except (IndexError, OSError):
                    raise ValueError("Couldn't find any projects @ '%s'" % root)

            self._state["projectName"] = current_project
            self._state["root"] = root

            self._state.to_ready()

        def _on_success():
            self.select_project(self._state["projectName"])
            on_success()

        def _on_failure(error):
            self.error(error)

        self._state.to_booting()
        util.defer(do, on_success=_on_success, on_failure=_on_failure)

    @util.async_
    def launch(self, **kwargs):
        def do():
            app_name = self._state["appName"]
            rez_context = self._state["rezContexts"][app_name]
            rez_app = self._state["rezApps"][app_name]

            self.info("Found app: %s=%s" % (
                rez_app.name, rez_app.version
            ))

            app_model = self._models["apps"]
            app_index = app_model.findIndex(app_name)

            tool_name = kwargs.get(
                "command", app_model.data(app_index, "tool"))
            is_detached = kwargs.get(
                "detached", app_model.data(app_index, "detached"))

            assert tool_name

            overrides = self._models["packages"]._overrides
            disabled = self._models["packages"]._disabled

            self.info(
                "Launching %s%s.." % (
                    tool_name, " (detached)" if is_detached else "")
            )

            cmd = Command(
                context=rez_context,
                command=tool_name,
                package=rez_app,
                overrides=overrides,
                disabled=disabled,
                detached=is_detached,
                parent=self
            )

            cmd.stdout.connect(self.info)
            cmd.stderr.connect(self.error)

            self._state["commands"].append(cmd)
            self._models["commands"].append(cmd)

            self._state.store("startupApplication", app_name)
            self._state.store("app/%s/lastUsed" % app_name, time.time())
            self._state.to_launching()

        self._state.to_loading()
        util.delay(do)

    def debug(self, message):
        log.debug(message)
        self.logged.emit(message, logging.DEBUG)

    def info(self, message):
        log.info(message)
        self.logged.emit(message, logging.INFO)

    def warning(self, message):
        log.warning(message)
        self.logged.emit(message, logging.WARNING)

    def error(self, message):
        log.error(message)
        self.logged.emit(message, logging.ERROR)

    @util.cached
    def list_projects(self, root=None):
        root = root or self._state["root"]

        try:
            _, dirs, files = next(os.walk(root))
        except StopIteration:
            self.error("Could not find projects in %s" % root)
            return []

        # Packages use _ in place of -
        projects = [p.replace("-", "_") for p in dirs]

        return projects

    @util.async_
    def select_project(self, project_name, version=None):
        # Wipe existing data
        self._models["apps"].reset()
        self._models["context"].reset()
        self._models["environment"].reset()
        self._models["projectVersions"].setStringList([])

        def on_apps_found(apps):
            self._models["apps"].reset(apps)

            before = self._state["projectName"] or ""
            self._state["projectName"] = project_name
            self.project_changed.emit(before, project_name)

            self._state.to_ready()

        def on_apps_not_found(error, trace):
            print("on_apps_not_found")
            self._state.to_noapps()
            print(trace)

        def on_project_found(project):
            if not project:
                return self._state.to_noproject()

            # Continue the pipeline
            util.defer(
                self._find_apps,
                args=[project],
                on_success=on_apps_found,
                on_failure=on_apps_not_found,
            )

        def on_project_not_found(error, trace):
            if isinstance(error, rez.exceptions.PackageNotFoundError):
                self._state["error"] = error.value
                self.error(error.value)
                self._state.to_pkgnotfound()

            elif isinstance(error, rez.exceptions.ResolveError):
                self._state["error"] = error.value
                self.error(error.value)
                self._state.to_notresolved()

            elif isinstance(error, rez.vendor.version.util.VersionError):
                self._state["error"] = str(error)
                self.error(str(error))
                self._state.to_notresolved()

            elif isinstance(error, AssertionError):
                self._state["error"] = str(error)
                self.error(str(error))
                self._state.to_noapps()

            else:
                self._state["error"] = str(error)
                self.error(str(error))
                self._state.to_notresolved()

        self._state.to_loading()

        util.defer(
            self._find_project,
            args=[project_name, version],
            on_success=on_project_found,
            on_failure=on_project_not_found,
        )

    def select_application(self, app_name):
        self._state["appName"] = app_name
        self.info("%s selected" % app_name)

        try:
            context = self.context(app_name)
            environ = self.environ(app_name)
            packages = self.resolved_packages(app_name)

        except Exception:
            self._models["packages"].reset()
            self._models["context"].reset()
            self._models["environment"].reset()
            raise

        self._models["packages"].reset(packages)
        self._models["context"].load(context)
        self._models["environment"].load(environ)

    def select_tool(self, tool_name):
        self.debug("%s selected" % tool_name)
        self._state["tool"] = tool_name

    def _find_project(self, project_name, version):
        try:
            versions = self._state["rezProjects"][project_name]

        except KeyError:
            it = iter_packages(project_name)
            versions = sorted(it, key=lambda x: x.version, reverse=True)

            # Store for next time
            self._state["rezProjects"][project_name] = versions

        try:
            latest = versions[0]
        except IndexError:
            return None

        self._models["projectVersions"].setStringList([
            str(pkg.version) for pkg in versions
        ])

        return latest

    def _find_apps(self, project):
        # Each app has a unique context relative the current project
        # Find it, and keep track of it.

        apps = []

        if self._state.retrieve("showAllApps") and LAUNCHAPP_APPS:
            apps = os.listdir(LAUNCHAPP_APPS)

        if not apps:
            apps = []
            for req in project.requires:
                if not req.weak:
                    continue

                apps += [req.name]

        # Clear existing
        self._state["rezContexts"] = {}

        # TODO: Separate this, it may take a while if not memcached,
        #   and the user needs to know what's going on.
        contexts = odict()
        with util.timing() as t:
            for app_name in apps:
                request = [project.name, app_name]
                self.info("Resolving request: %s" % " ".join(request))

                rule = rez.package_filter.Rule.parse_rule("*.beta")
                PackageFilterList = rez.package_filter.PackageFilterList
                package_filter = PackageFilterList.singleton.copy()
                package_filter.add_exclusion(rule)

                try:
                    context = ResolvedContext(request,
                                              package_filter=package_filter)
                except rez.exceptions.RezError as e:
                    self.error(str(e))
                    continue

                if not context.success:
                    description = context.failure_description
                    self.error(description)
                    continue
                    # raise rez.exceptions.ResolveError(description)

                contexts[app_name] = context

        # Associate a Rez package with an app
        for app_name, rez_context in contexts.items():
            rez_pkg = next(pkg for pkg in rez_context.resolved_packages
                           if pkg.name == app_name)
            self._state["rezApps"][app_name] = rez_pkg

        self.debug("Resolved all contexts in %.2f seconds" % t.duration)

        # Find resolved app version
        # E.g. maya -> maya-2018.0.1
        app_packages = []
        show_hidden = self._state.retrieve("showHiddenApps")
        for app_name, context in contexts.items():
            for package in context.resolved_packages:
                if package.name in apps:
                    break
            else:
                # This cannot happen and would be a bug
                raise ValueError(
                    "Could not find package for app %s" % app_name
                )

            hidden = getattr(package, "_data", {}).get("hidden", False)
            if hidden and not show_hidden:
                continue

            app_packages += [package]

        self._state["rezContexts"] = contexts
        return app_packages


class BrokenPackage(object):
    def __str__(self):
        return self.name

    def __init__(self, name):
        self.name = name


class Command(QtCore.QObject):
    stdout = QtCore.Signal(str)
    stderr = QtCore.Signal(str)
    killed = QtCore.Signal()

    def __str__(self):
        return "Command('%s')" % self.cmd

    def __init__(self,
                 context,
                 command,
                 package,
                 overrides=None,
                 disabled=None,
                 detached=True,
                 parent=None):
        super(Command, self).__init__(parent)

        self.overrides = overrides or {}
        self.disabled = disabled or {}

        self.context = context
        self.app = package
        self.popen = None
        self.detached = detached

        # `cmd` rather than `command`, to distinguish
        # between class and argument
        self.cmd = command

        self.nicecmd = "rez env {request} -- {cmd}".format(
            request=" ".join(
                str(pkg)
                for pkg in context.requested_packages()
            ),
            cmd=command
        )

        self._running = False

        # Launching may take a moment, and there's no need
        # for the user to wait around for that to happen.
        thread = threading.Thread(target=self.execute)
        thread.daemon = True
        thread.start()

        self.thread = thread

    @property
    def pid(self):
        return self.popen.pid

    def execute(self):
        kwargs = {
            "command": self.cmd,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "detached": self.detached,
        }

        context = self.context

        # Output to console
        log.info("Console command: %s" % self.nicecmd)

        if self.overrides or self.disabled:
            # Apply overrides to a new context, to preserve the original
            context = ResolvedContext(context.requested_packages())
            packages = context.resolved_packages[:]

            name_to_package_lut = {
                package.name: package
                for package in packages
            }

            for name, version in self.overrides.items():
                try:
                    original = name_to_package_lut[name]
                except KeyError:
                    # Override not part of this context, that's fine
                    continue

                # Find a replacement, taking implciit variants into account
                request = "%s-%s" % (name, version)
                replacement = ResolvedContext([request])
                replacement = {
                    package.name: package
                    for package in replacement.resolved_packages
                }[name]

                packages.remove(original)
                packages.append(replacement)

                log.info("Overriding %s.%s -> %s.%s" % (
                    name, original.version,
                    name, replacement.version
                ))

            for package_name in self.disabled:
                package = name_to_package_lut[package_name]

                try:
                    packages.remove(package)
                except ValueError:
                    # It wasn't in there, and that's OK
                    continue

                log.info("Disabling %s" % package_name)

            context.resolved_packages[:] = packages

        self.popen = context.execute_shell(**kwargs)

        for target in (self.listen_on_stdout,
                       self.listen_on_stderr):
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()

    def is_running(self):
        # Normally, you'd be able to determine whether a Popen instance was
        # still running by querying Popen.poll() == None, but Rez may or may
        # not use `Popen(shell=True)` which throws this mechanism off. Instead,
        # we'll let an open pipe to STDOUT determine whether or not a process
        # is currently running.
        return self._running

    def listen_on_stdout(self):
        self._running = True
        for line in iter(self.popen.stdout.readline, ""):
            self.stdout.emit(line.rstrip())
        self._running = False
        self.killed.emit()

    def listen_on_stderr(self):
        for line in iter(self.popen.stderr.readline, ""):
            self.stderr.emit(line.rstrip())
