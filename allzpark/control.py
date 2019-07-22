"""Orchestrates view.py and model.py"""

import os
import time
import errno
import shutil
import logging
import tempfile
import threading
import traceback
import subprocess

from collections import OrderedDict as odict

from .vendor.Qt import QtCore
from .vendor import transitions
from . import model, util, allzparkconfig

# Third-party dependencies
from . import _rezapi as rez

# Optional third-party dependencies
try:
    from localz import lib as localz
except ImportError:
    localz = None

log = logging.getLogger(__name__)
Latest = None  # Enum


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
            "appRequest": storage.value("startupApplication"),

            # String or callable, returning list of project names
            "root": None,

            # Current error, if any
            "error": None,

            # Currently commands applications
            "commands": [],

            # Previously loaded project Rez packages
            "rezProjects": {},

            # Currently loaded Rez contexts
            "rezContexts": {},
            "rezApps": odict(),
            "fullCommand": "rez env",
            "serialisationMode": (
                storage.value("serialisationMode") or "used_request"
            ),
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

    def retrieve(self, key, default=None):
        """Read from persistent storage

        Arguments:
            key (str): Name of variable

        """

        value = self._storage.value(key)

        if value is None:
            value = default

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
    resetted = QtCore.Signal()

    # One or more packages have changed on disk
    repository_changed = QtCore.Signal()

    project_changed = QtCore.Signal(
        str, str, bool)  # project, version, refreshed

    # The current command to launch an application has changed
    command_changed = QtCore.Signal(str)  # command

    patch_changed = QtCore.Signal(str)  # full patch string

    states = [
        _State("booting", help="ALLZPARK is booting, hold on"),
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
            "projectNames": QtCore.QStringListModel(),
            "apps": model.ApplicationModel(),

            # Docks
            "packages": model.PackagesModel(self),
            "context": model.JsonModel(),
            "environment": model.EnvironmentModel(),
            "commands": model.CommandsModel(),
        }

        timers = {
            "commandsPoller": QtCore.QTimer(self),
            "cacheCleaner": QtCore.QTimer(self),
        }

        timers["commandsPoller"].timeout.connect(self.on_tasks_polled)
        timers["commandsPoller"].start(500)

        timeout = int(state.retrieve("clearCacheTimeout", 1))
        timers["cacheCleaner"].timeout.connect(self.on_cache_cleared)
        timers["cacheCleaner"].start(timeout * 1000)

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
        return self._state["appRequest"]

    @property
    def current_tool(self):
        return self._state["tool"]

    def context(self, app_request):
        return self._state["rezContexts"][app_request].to_dict()

    def environ(self, app_request):
        return self._state["rezContexts"][app_request].get_environ()

    def resolved_packages(self, app_request):
        return self._state["rezContexts"][app_request].resolved_packages

    def find(self, package_name, callback=lambda result: None):
        return util.defer(
            rez.find, args=[package_name],
            on_success=callback
        )

    # ----------------
    # Events
    # ----------------

    def on_tasks_polled(self):
        self._models["commands"].poll()

    def on_cache_cleared(self):
        for path in self._package_paths():
            repo = rez.package_repository_manager.get_repository(path)
            repo.clear_caches()

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

        if rez.RexError is type:
            # These are re-raised as a more specific
            # exception, e.g. RexUndefinedVariableError
            pass

        if rez.RexUndefinedVariableError is type:
            pass

        if rez.PackageCommandError is type:
            pass

        self.error("".join(traceback.format_tb(tb)))
        self.error(str(value))
        self._state.to_errored()

    # ----------------
    # Methods
    # ----------------

    def update_command(self, mode=None):
        if self._state["appRequest"] not in self._state["rezContexts"]:
            return

        if mode:
            self._state["serialisationMode"] = mode
            self._state.store("serialisationMode", mode)

        mode = self._state["serialisationMode"]
        app = self._state["appRequest"]
        context = self._state["rezContexts"][app]
        tool = self._state["tool"]
        exclude = allzparkconfig.exclude_filter

        if mode == "used_resolve":
            packages = [
                "%s==%s" % (pkg.name, pkg.version)
                for pkg in context.resolved_packages
            ]

        else:
            packages = [str(pkg) for pkg in context.requested_packages()]

        command = ["rez", "env"]
        command += packages

        if exclude:
            command += ["--exclude", exclude]

        # Ensure consistency during re-resolve
        # Important for submitting contexts across
        # machines at different times
        command += ["--time", str(context.timestamp)]

        if localz and not self._state.retrieve("useLocalizedPackages", True):
            paths = os.pathsep.join(self._package_paths())
            command += ["--paths"] + ["\"%s\"" % paths]

        elif not self._state.retrieve("useDevelopmentPackages"):
            command += ["--no-local"]

        command += ["--", tool]

        self._state["fullCommand"] = " ".join(command)
        self.command_changed.emit(self._state["fullCommand"])

    @util.async_
    def reset(self, root=None, on_success=lambda: None):
        """Initialise controller with `root`

        Projects are listed at `root` and matched
        with its corresponding Rez package.

        Arguments:
            root (str): Absolute path to projects on disk, or callable
                returning names of projects

        """

        self.info("Resetting..")
        root = root or self._state["root"]
        assert root, "Tried resetting without a root, this is a bug"

        def do():
            projects = dict()
            default_project = None

            for name in self.list_projects(root):

                # Find project package
                package = None
                it = rez.find(name, paths=self._package_paths())
                it = sorted(
                    it,

                    # Make e.g. 1.10 appear after 1.9
                    key=lambda p: util.natural_keys(str(p.version))
                )

                for package in it:

                    if name not in projects:
                        projects[name] = dict()

                    projects[name][str(package.version)] = package
                    projects[name][Latest] = package

                if package is None:
                    package = model.BrokenPackage(name)
                    projects[name] = {
                        "0.0": package,
                        Latest: package,
                    }

                # Default to latest of last
                default_project = name

            self._state["rezProjects"].update(projects)
            self._models["projectNames"].setStringList(list(projects))
            self._models["projectNames"].layoutChanged.emit()

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
                current_project = default_project

            # Fallback
            if not current_project:
                current_project = "No project"

            self._state["projectName"] = current_project
            self._state["root"] = root

            self._state.to_ready()
            self.resetted.emit()

        def _on_success():
            self.select_project(self._state["projectName"])
            on_success()

        def _on_failure(error, trace):
            self.error("There was a problem")
            self.error(trace)

        self._state["rezContexts"].clear()
        self._state["rezApps"].clear()

        self._state.to_booting()
        util.defer(
            do,
            on_success=_on_success,
            on_failure=_on_failure
        )

    def patch(self, request):
        self.debug("Patching %s.." % request)
        current = self._state.retrieve("patch", "").split()
        if request not in current:
            current += [request]
        self._state.store("patch", " ".join(current))
        self.reset()

    @util.async_
    def launch(self, **kwargs):
        def do():
            app_request = self._state["appRequest"]
            rez_context = self._state["rezContexts"][app_request]
            rez_app = self._state["rezApps"][app_request]

            self.info("Found app: %s=%s" % (
                rez_app.name, rez_app.version
            ))

            app_model = self._models["apps"]
            app_index = app_model.findIndex(app_request)

            tool_name = kwargs.get(
                "command", app_model.data(app_index, "tool"))
            is_detached = kwargs.get(
                "detached", app_model.data(app_index, "detached"))

            assert tool_name, (
                "There should have been at least one tool name. "
                "This is a bug"
            )

            overrides = self._models["packages"]._overrides
            disabled = self._models["packages"]._disabled
            environ = self._state.retrieve("userEnv", {})

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
                environ=environ,
                parent=self
            )

            cmd.stdout.connect(self.info)
            cmd.stderr.connect(self.error)

            self._state["commands"].append(cmd)
            self._models["commands"].append(cmd)

            self._state.store("app/%s/lastUsed" % app_request, time.time())
            self._state.to_launching()

        self._state.to_loading()
        util.delay(do)

    def localize(self, name):
        tempdir = tempfile.mkdtemp()

        def do():
            self.info("Resolving %s.." % name)
            variant = localz.resolve(name)[0]  # Guaranteed to be one

            try:
                self.info("Preparing %s.." % name)
                copied = localz.prepare(variant, tempdir, verbose=2)[0]

                self.info("Computing size..")
                size = localz.dirsize(tempdir) / (10.0 ** 6)  # mb

                self.info("Localising %.2f mb.." % size)
                result = localz.localize(copied,
                                         localz.localized_packages_path(),
                                         verbose=2)

                self.info("Localised %s" % result)

            finally:
                self.info("Cleaning up..")
                shutil.rmtree(tempdir)

        def on_success(result):
            self.repository_changed.emit()

        def on_failure(error, trace):
            self.error(trace)

        util.defer(do,
                   on_success=on_success,
                   on_failure=on_failure)

    def delocalize(self, name):
        def do():
            item = self._models["packages"].find(name)
            package = item["package"]
            self.info("Delocalizing %s" % package.root)
            localz.delocalize(package)

        def on_success(result):
            self.repository_changed.emit()

        def on_failure(error, trace):
            self.error(trace)

        util.defer(do,
                   on_success=on_success,
                   on_failure=on_failure)

    def _localize_status(self, package):
        """Return status of localisation"""
        return None

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
        self.logged.emit(str(message), logging.ERROR)

    def list_projects(self, root=None):
        root = root or self._state["root"]
        assert root, "Tried listing without a root, this is a bug"

        if isinstance(root, (tuple, list)):
            return root

        try:
            if callable(root):
                projects = root()

            else:
                _, projects, _ = next(os.walk(root))

                # Support directory names that use dash in place of underscore
                projects = [p.replace("-", "_") for p in projects]

        except Exception:
            if log.level < logging.INFO:
                traceback.print_exc()

            self.error("Could not find projects in %s" % root)
            projects = []

        return projects

    @util.async_
    def select_project(self, project_name, version_name=Latest):

        # Wipe existing data
        self._models["apps"].reset()
        self._models["context"].reset()
        self._models["environment"].reset()
        self._models["packages"].reset()
        self._models["projectVersions"].setStringList([])

        def on_apps_found(apps):
            self._models["apps"].reset(apps)
            self._state["projectName"] = project_name

            refreshed = self._state["projectName"] == project_name
            self.project_changed.emit(
                str(active_project.name),
                str(active_project.version),
                refreshed
            )

            self._state.to_ready()

        def on_apps_not_found(error, trace):
            self._state.to_noapps()
            self.error(trace)

        try:
            project_versions = self._state["rezProjects"][project_name]
            active_project = project_versions[version_name]

            # Update versions model
            versions = list(filter(None, project_versions))  # Exclude "Latest"
            self._models["projectVersions"].setStringList(versions)

            self._state.to_loading()
            util.defer(
                self._list_apps,
                args=[active_project],
                on_success=on_apps_found,
                on_failure=on_apps_not_found,
            )

        except KeyError:
            self._state.to_notresolved()

    def select_application(self, app_request):
        self._state["appRequest"] = app_request
        self.info("%s selected" % app_request)

        try:
            context = self.context(app_request)
            environ = self.environ(app_request)
            packages = self.resolved_packages(app_request)

        except Exception:
            self._models["packages"].reset()
            self._models["context"].reset()
            self._models["environment"].reset()
            raise

        self._models["packages"].reset(packages)
        self._models["context"].load(context)
        self._models["environment"].load(environ)

        tools = self._models["apps"].find(app_request)["tools"]
        self._state["tool"] = tools[0]

        # Use this application on next launch or change of project
        self.update_command()
        self._state.store("startupApplication", app_request)

    def select_tool(self, tool_name):
        self.debug("%s selected" % tool_name)
        self._state["tool"] = tool_name
        self.update_command()

    def _package_paths(self):
        """Return all package paths, relative the current state of the world"""

        paths = util.normpaths(*rez.config.packages_path)

        # Optional development packages
        if not self._state.retrieve("useDevelopmentPackages"):
            self.debug("Excluding development packages")
            paths = util.normpaths(*rez.config.nonlocal_packages_path)

        # Optional package localisation
        if localz and not self._state.retrieve("useLocalizedPackages", True):
            self.debug("Excluding localized packages")
            path = localz.localized_packages_path()

            try:
                paths.remove(util.normpath(path))
            except ValueError:
                # It may not be part of the path
                self.warning(
                    "%s was not found on your "
                    "package path." % path
                )

        return paths

    def _list_apps(self, project):
        # Each app has a unique context relative the current project
        # Find it, and keep track of it.

        apps = []
        _apps = allzparkconfig.applications

        paths = self._package_paths()

        if self._state.retrieve("showAllApps") and not _apps:
            self.info("Requires allzparkconfig.applications")

        elif self._state.retrieve("showAllApps"):
            if isinstance(_apps, (tuple, list)):
                apps = _apps

            else:
                try:
                    if callable(_apps):
                        apps = _apps()
                    else:
                        apps = os.listdir(_apps)
                except OSError as e:
                    if e.errno not in (errno.ENOENT,
                                       errno.EEXIST,
                                       errno.ENOTDIR):
                        raise

                    self.info("Could not show all apps, "
                              "missing `allzparkconfig.applications`")

        if not apps:
            apps[:] = allzparkconfig.applications_from_package(project)

        # Strip the "weak" property of the request, else iter_packages
        # isn't able to find the requested versions.
        apps = [rez.PackageRequest(req.strip("~")) for req in apps]

        # Expand versions into their full range
        # E.g. maya-2018|2019 == ["maya-2018", "maya-2019"]
        all_apps = list()
        for request in apps:
            all_apps += rez.find(
                request.name,
                range_=request.range,
                paths=paths
            )

        # Optional patch
        patch = self._state.retrieve("patch", "").split()

        # Optional filtering
        PackageFilterList = rez.PackageFilterList
        package_filter = PackageFilterList.singleton.copy()
        if allzparkconfig.exclude_filter:
            rule = rez.Rule.parse_rule(allzparkconfig.exclude_filter)
            package_filter.add_exclusion(rule)

        contexts = odict()
        with util.timing() as t:
            for app_package in all_apps:
                variants = list(project.iter_variants())
                variant = variants[0]

                if len(variants) > 1:
                    # Unsure of whether this is desirable. It would enable
                    # a project per platform, or potentially other kinds
                    # of special-purpose situations. If you see this,
                    # and want this, submit an issue with your use case!
                    self.warning(
                        "Projects with multiple variants are unsupported. "
                        "Using first found: %s" % variant
                    )

                app_request = "%s==%s" % (app_package.name,
                                          app_package.version)

                request = [variant.qualified_package_name, app_request]
                self.info("Resolving request: %s" % " ".join(request))

                try:
                    context = rez.env(
                        request,
                        package_paths=paths,
                        package_filter=package_filter,
                    )

                except rez.RezError:
                    context = model.BrokenContext(app_request, request)
                    context.failure_description = traceback.format_exc()
                    self.error(traceback.format_exc())

                if not context.success:
                    # Happens on failed resolve, e.g. version conflict
                    description = context.failure_description
                    context = model.BrokenContext(app_request, request)
                    context.failure_description = description
                    self.error(description)

                if patch and not isinstance(context, model.BrokenContext):
                    self.info("Patching request: %s" % " ".join(request))
                    request = context.get_patched_request(patch)
                    context = rez.env(
                        request,
                        package_paths=paths,
                        package_filter=(
                            package_filter
                            if self._state.retrieve("patchWithFilter", True)
                            else None
                        )
                    )

                contexts[app_request] = context

        # Associate a Rez package with an app
        for app_request, rez_context in contexts.items():
            try:
                rez_pkg = next(
                    pkg
                    for pkg in rez_context.resolved_packages
                    if "%s==%s" % (pkg.name, pkg.version) == app_request
                )

            except StopIteration:
                # Can happen with a patched context, where the application
                # itself is patched away. E.g. "^maya". This is a user error.
                rez_pkg = model.BrokenPackage(app_request)

            self._state["rezApps"][app_request] = rez_pkg

        self.debug("Resolved all contexts in %.2f seconds" % t.duration)

        # Find resolved app version
        # E.g. maya -> maya-2018.0.1
        app_packages = []
        show_hidden = self._state.retrieve("showHiddenApps")
        for app_request, context in contexts.items():
            for package in context.resolved_packages:
                if package.name in [a.name for a in all_apps]:
                    break
            else:
                raise ValueError(
                    "Could not find package for app %s" % app_request
                )

            data = allzparkconfig.metadata_from_package(package)
            hidden = data.get("hidden", False)

            if hidden and not show_hidden:
                package.hidden = True
                continue

            if isinstance(context, model.BrokenContext):
                package.broken = True

            app_packages += [package]

        self._state["rezContexts"] = contexts
        return app_packages


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
                 environ=None,
                 parent=None):
        super(Command, self).__init__(parent)

        self.overrides = overrides or {}
        self.disabled = disabled or {}
        self.environ = environ or {}

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
        if self.popen.poll is None:
            return self.popen.pid

    def execute(self):
        kwargs = {
            "command": self.cmd,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "detached": self.detached,
            "parent_environ": None,
        }

        context = self.context

        # Output to console
        log.info("Console command: %s" % self.nicecmd)

        if self.overrides or self.disabled:
            # Apply overrides to a new context, to preserve the original
            context = rez.env(context.requested_packages())
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
                replacement = rez.env([request])
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

        if self.environ:
            # Inject user environment
            #
            # NOTE: Rez takes precendence on environment, so a user
            # cannot edit the environment in such a way that packages break.
            # However it also means it cannot edit variables also edited
            # by a package. Win some lose some
            kwargs["parent_environ"] = dict(os.environ, **self.environ)

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
