"""Orchestrates view.py and model.py"""

import os
import sys
import time
import json
import errno
import shutil
import logging
import tempfile
import threading
import traceback
import subprocess

from collections import OrderedDict as odict

from .vendor.Qt import QtCore, QtGui
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

Latest = model.Latest  # Enum
NoVersion = model.NoVersion


class State(dict):
    """Transient, persistent and machine for state

    The state is used to keep track of which applications
    is the "current" one, along with managing the current
    "state" such as whether the application is busy loading,
    whether it's ready for user input. It also manages persistent
    data, the kind that is stored until the next time the
    application is launched.

    """

    def __init__(self, ctrl, storage, parent_environ=None):
        super(State, self).__init__({
            "profileName": storage.value("startupProfile"),
            "appRequest": storage.value("startupApplication"),

            # list or callable, returning list of profile names
            "root": None,

            # Current error, if any
            "error": None,

            # Currently commands applications
            "commands": [],

            # Previously loaded profile Rez packages
            "rezProfiles": {},

            # Currently loaded Rez contexts
            "rezContexts": {},

            # Cache, for performance only
            "rezEnvirons": {},

            # Parent environment for all applications
            "parentEnviron": parent_environ or {},

            # Cache environment testing result
            "testedEnvirons": {},

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
        self._ctrl.debug("Booting..")

    def on_enter_selectprofile(self):
        pass

    def on_enter_resolving(self):
        pass

    def on_enter_launching(self):
        self._ctrl.debug("Application is being launched..")
        util.delay(self.to_ready, 500)

    def on_enter_noapps(self):
        profile = self["profileName"]
        self._ctrl.debug("No applications were found for %s" % profile)

    def on_enter_loading(self):
        self._ctrl.debug("Loading..")

    def on_enter_ready(self):
        self._ctrl.debug("Ready")


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


class _Stream(object):
    def __init__(self, ctrl, stream, level):
        self._ctrl = ctrl
        self._stream = stream
        self._level = level

    def write(self, text):
        self._stream.write(text) if self._stream else None
        self._ctrl.logged.emit(text, self._level)

    def fileno(self):
        return 0

    def close(self):
        return


class Controller(QtCore.QObject):
    state_changed = QtCore.Signal(_State)
    logged = QtCore.Signal(str, int)  # message, level
    resetted = QtCore.Signal()

    # One or more packages have changed on disk
    repository_changed = QtCore.Signal()

    profile_changed = QtCore.Signal(
        str, object, bool)  # profile, version, refreshed

    application_changed = QtCore.Signal()

    # The current command to launch an application has changed
    command_changed = QtCore.Signal(str)  # command

    patch_changed = QtCore.Signal(str)  # full patch string

    running_cmd_updated = QtCore.Signal(int)

    states = [
        _State("booting", help="ALLZPARK is booting, hold on"),
        _State("resolving", help="Rez is busy resolving a context"),
        _State("loading", help="Something is taking a moment"),
        _State("errored", help="Something has gone wrong"),
        _State("launching", help="An application is launching"),
        _State("ready", help="Awaiting user input"),
        _State("noprofiles", help="Allzpark did not find any profiles at all"),
        _State("noapps", help="There were no applications to choose from"),
        _State("notresolved", help="Rez couldn't resolve a request"),
        _State("pkgnotfound", help="One or more packages was not found"),
    ]

    def __init__(self,
                 storage,
                 parent_environ=None,
                 stdio=None,
                 stderr=None,
                 parent=None):

        super(Controller, self).__init__(parent)

        state = State(self, storage, parent_environ)

        models = {
            "apps": model.ApplicationModel(),
            "profileVersions": QtCore.QStringListModel(),

            # Docks
            "profiles": model.ProfileModel(),
            "packages": model.PackagesModel(self),
            "context": model.ContextModel(),
            "environment": model.EnvironmentModel(),
            "parentenv": model.EnvironmentModel(),
            "diagnose": model.EnvironmentModel(),
            "commands": model.CommandsModel(),
        }

        timers = {
            "commandsPoller": QtCore.QTimer(self),
        }

        timers["commandsPoller"].timeout.connect(self.on_tasks_polled)
        timers["commandsPoller"].start(500)

        models["parentenv"].load(state["parentEnviron"].copy())

        # Initialize the state machine
        self._machine = transitions.Machine(
            model=state,
            states=self.states,
            initial="booting",
            after_state_change=[self.on_state_changed],

            # Add "on_enter_<state name>" to model
            auto_transitions=True,
        )

        self._timers = timers
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
    def timers(self):
        return self._timers

    @property
    def state(self):
        return self._state

    @property
    def current_error(self):
        return self._state["error"]

    @property
    def current_profile(self):
        return self._state["profileName"]

    @property
    def current_application(self):
        return self._state["appRequest"]

    @property
    def current_tool(self):
        return self._state["tool"]

    def context(self, app_request):
        return self._state["rezContexts"][app_request].to_dict()

    def parent_environ(self):
        environ = self._state["parentEnviron"].copy()
        # Inject user environment
        #
        # NOTE: Rez takes precendence on environment, so a user
        # cannot edit the environment in such a way that packages break.
        # However it also means it cannot edit variables also edited
        # by a package. Win some lose some
        environ = dict(environ, **self._state.retrieve("userEnv", {}))

        return environ

    def environ(self, app_request):
        """Fetch the environment of a context

        NOTE: These can get very expensive. They call on every
              package.py:commands() in a resolved context, which can
              be in the tens to hundreds. Add to that the fact that
              these functions can perform any arbitrary task, including
              writing to disk or performing expensive calculations,
              such as resolving their own contexts for various reasons.

        TODO: This should be async, the GUI should help the user
              understand that the environment is loading and is
              going to be ready soon. They should also only incur
              cost when the user is actually looking at the
              environment tab.

        """

        env = self._state["rezEnvirons"]
        ctx = self._state["rezContexts"]

        try:
            return env[app_request]

        except KeyError:
            context = ctx[app_request]
            parent_env = self.parent_environ()
            try:
                environ = context.get_environ(parent_environ=parent_env)

            except rez.ResolvedContextError:
                return {
                    "error": "Failed context"
                }
            else:
                env[app_request] = environ
                return environ

    def resolved_packages(self, app_request):
        return self._state["rezContexts"][app_request].resolved_packages

    # ----------------
    # Events
    # ----------------

    def on_tasks_polled(self):
        running_count = self._models["commands"].poll()
        self.running_cmd_updated.emit(running_count)

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

        # Potentially overridden by the below
        self._state["error"] = "".join(
            traceback.format_tb(tb) + [str(value)]
        )
        self._state.to_errored()
        self.error(self._state["error"])

        if rez.PackageNotFoundError is type:
            package = value.value.rsplit(": ", 1)[-1]
            paths = self._package_paths()
            message = """
                <h2><font color=\"red\">:(</font></h2>

                Package '{package}' is required by this profile,
                but could <font color=\"red\">not be found.</font>
                <br>
                <br>
                I searched in these paths:
                {paths}
            """

            self._state["error"] = message.format(
                package=package,
                paths="<ul>%s</ul>" % "".join(
                    "<li>%s</li>" % path for path in paths
                )
            )

            self._state.to_noapps()
            return True

        elif rez.PackageFamilyNotFoundError is type:
            # package family not found: occoc (searched: C:\)
            _, package, paths = value.value.split(": ", 2)
            package = package.split(" (", 1)[0]
            paths = paths.rstrip(")").split("; ")  # Hard-coded pathsep in Rez

            message = """
                <h2><font color=\"red\">:(</font></h2>

                Package '{package}' is required by this profile,
                but could <font color=\"red\">not be found.</font>
                <br>
                <br>
                I searched in these paths:
                {paths}
            """

            self._state["error"] = message.format(
                package=package,
                paths="<ul>%s</ul>" % "".join(
                    "<li>%s</li>" % path for path in paths
                )
            )

            self._state.to_noapps()
            return True

        elif rez.ResolvedContextError is type:
            # Cannot perform operation in a failed context
            self.error(str(value))
            self._state.to_ready()
            return True

        elif rez.RexError is type:
            # These are re-raised as a more specific
            # exception, e.g. RexUndefinedVariableError
            self._state.to_errored()

        elif rez.RexUndefinedVariableError is type:
            self._state.to_errored()

        elif rez.PackageCommandError is type:
            self._state.to_errored()

        elif rez.PackageRequestError is type:
            message = "<h2><font color=\"red\">:(</font></h2>%s"
            self._state["error"] = message % value
            self._state.to_noapps()

        self.error(self._state["error"])

    # ----------------
    # Methods
    # ----------------

    def stdio(self, stream, level=logging.INFO):
        return _Stream(self, stream, level)

    def find(self, family, range_=None):
        """Find packages, relative Allzpark state

        Arguments:
            family (str): Name of package
            range_ (str): Range, e.g. "1" or "==0.3.13"

        """

        package_filter = self._package_filter()
        paths = self._package_paths()
        it = rez.find(family, range_, paths=paths)
        it = sorted(
            it,

            # Make e.g. 1.10 appear after 1.9
            key=lambda p: util.natural_keys(str(p.version))
        )

        for pkg in it:
            if package_filter.excludes(pkg):
                self.debug("Excluding %s==%s.." % (pkg.name, pkg.version))
                continue

            yield pkg

    def env(self, requests, use_filter=True):
        """Resolve context, relative Allzpark state

        Arguments:
            requests (list): Fully formatted request, including any
                number of packages. E.g. "six==1.2 PySide2"
            use_filter (bool, optional): Whether or not to apply
                the current package_filter

        """

        package_filter = self._package_filter()
        paths = self._package_paths()

        return rez.env(
            requests,
            package_paths=paths,
            package_filter=package_filter if use_filter else None
        )

    def update_command(self, mode=None):
        if mode:
            self._state["serialisationMode"] = mode
            self._state.store("serialisationMode", mode)

        if self._state["appRequest"] not in self._state["rezContexts"]:
            # In this case, we have no context, so there
            # is very little to actually try and reproduce
            self._state["fullCommand"] = ""
            return self.command_changed.emit("")

        mode = self._state["serialisationMode"]
        app = self._state["appRequest"]
        context = self._state["rezContexts"][app]
        tool = self._state["tool"]
        exclude = allzparkconfig.exclude_filter

        if mode == "used_resolve":
            packages = [
                "%s==%s" % (pkg.name, pkg.version)
                for pkg in context.resolved_packages or []
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

    def _package_filter(self):
        package_filter = rez.PackageFilterList.singleton.copy()

        if allzparkconfig.exclude_filter:
            rule = rez.Rule.parse_rule(allzparkconfig.exclude_filter)
            package_filter.add_exclusion(rule)

        return package_filter

    @util.async_
    def reset(self, root=None, on_success=lambda: None):
        """Initialise controller with `root`

        Profiles are listed at `root` and matched
        with its corresponding Rez package.

        Arguments:
            root (list, callable): A list of profile names, or a callable
                returning names of profiles.
            on_success (callable): Callback on reset completed.

        """

        self.info("Resetting..")
        root = root or self._state["root"]
        assert root, "Tried resetting without a root, this is a bug"

        def do():
            profiles = dict()
            default_profile = None

            for name in self.list_profiles(root):

                # Find profile package
                package = None
                for package in self.find(name):

                    if name not in profiles:
                        profiles[name] = dict()

                    profiles[name][str(package.version)] = package
                    profiles[name][Latest] = package

                if package is None:
                    package = model.BrokenPackage(name)
                    profiles[name] = {
                        "0.0": package,
                        Latest: package,
                    }

                # Default to latest of last
                default_profile = name

            self._state["rezProfiles"].update(profiles)

            # On resetting after startup, there will be a
            # currently selected profile that may differ from
            # the startup profile.
            current_profile = self._state["profileName"]

            if current_profile and current_profile not in profiles:
                self.warning("Startup profile '%s' did not exist"
                             % current_profile)
                current_profile = None

            # The user has never opened the GUI before,
            # or user preferences has been wiped.
            if not current_profile:
                current_profile = default_profile

            self._models["profiles"].set_favorites(self)
            self._models["profiles"].set_current(current_profile)
            self._models["profiles"].reset(profiles)

            self._state["profileName"] = current_profile
            self._state["root"] = root

            self._state.to_ready()
            self.resetted.emit()

        def _on_success():
            profile = not self._state["profileName"]

            if profile:
                self._state.to_noprofiles()
            else:
                self.select_profile(profile)

            on_success()

        def _on_failure(error, trace):
            raise error

        self._state["rezContexts"].clear()
        self._state["rezEnvirons"].clear()
        self._state["rezApps"].clear()

        # Rez stores file listings and more
        # in memory, in addition to memcached.
        # This function clears the in-memory cache,
        # so that we can pick up new packages.
        rez.clear_caches()

        self._state.to_booting()
        util.defer(
            do,
            on_success=_on_success,
            on_failure=_on_failure
        )

    def patch(self, new):
        self.debug("Patching %s.." % new)

        new = rez.PackageRequest(new)
        old = odict(
            (rez.PackageRequest(req).name, rez.PackageRequest(req))
            for req in self._state.retrieve("patch", "").split()
        )

        if new.name in old:
            old.pop(new.name)

        if str(new.range):
            # Otherwise, let it return to the originally resolved value
            old[new.name] = new

        patch = " ".join(str(pkg) for pkg in old.values())
        self._state.store("patch", patch)
        self.reset()

    @util.async_
    def launch(self, **kwargs):
        def do():
            app_request = self._state["appRequest"]
            rez_context = self._state["rezContexts"][app_request]
            rez_app = self._state["rezApps"][app_request]

            self.debug("Found app: %s=%s" % (
                rez_app.name, rez_app.version
            ))

            app_model = self._models["apps"]
            app_index = app_model.findIndex(app_request)

            tool_name = kwargs.get(
                "command", app_model.data(app_index, "tool"))
            is_detached = kwargs.get(
                "detached", app_model.data(app_index, "detached"))
            stdout = kwargs.get("stdout", self.info)
            stderr = kwargs.get("stderr", self.error)

            assert tool_name, (
                "There should have been at least one tool name. "
                "This is a bug"
            )

            overrides = self._models["packages"]._overrides
            disabled = self._models["packages"]._disabled
            environ = self.parent_environ()

            self.debug(
                "Launching %s%s.." % (
                    tool_name, " (detached)" if is_detached else "")
            )

            def on_error(error):
                # Forward error from Command()
                raise error

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

            cmd.stdout.connect(stdout)
            cmd.stderr.connect(stderr)
            cmd.error.connect(on_error)

            cmd.execute()

            self._state["commands"].append(cmd)
            self._models["commands"].append(cmd)

            self._state.store("app/%s/lastUsed" % app_request, time.time())
            self._state.to_launching()

        self._state.to_loading()
        util.delay(do)

    def localize(self, name):
        tempdir = tempfile.mkdtemp()

        def do():
            self.debug("Resolving %s.." % name)
            variant = localz.resolve(name)[0]  # Guaranteed to be one

            try:
                self.debug("Preparing %s.." % name)
                copied = localz.prepare(variant, tempdir, verbose=2)[0]

                self.debug("Computing size..")
                size = localz.dirsize(tempdir) / (10.0 ** 6)  # mb

                self.debug("Localising %.2f mb.." % size)
                result = localz.localize(copied,
                                         localz.localized_packages_path(),
                                         verbose=2)

                self.debug("Localised %s" % result)

            finally:
                self.debug("Cleaning up..")
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
            self.debug("Delocalizing %s" % package.root)
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
        self.logged.emit(message, logging.DEBUG)

    def info(self, message):
        self.logged.emit(message, logging.INFO)

    def warning(self, message):
        self.logged.emit(message, logging.WARNING)

    def error(self, message):
        self.logged.emit(str(message), logging.ERROR)

    def list_profiles(self, root=None):
        root = root or self._state["root"]
        assert root, "Tried listing without a root, this is a bug"

        if isinstance(root, (tuple, list)):
            profiles = root

        elif callable(root):
            try:
                profiles = root()

            except Exception:
                if log.level < logging.INFO:
                    traceback.print_exc()

                self.error("Could not find profiles in %s" % root)
                profiles = []

        else:
            raise TypeError("Argument 'root' should be either list type or "
                            "callable.")

        # Facilitate accidental empty family names, e.g. None or ''
        profiles = list(filter(None, profiles))

        return profiles

    @util.async_
    def select_profile(self, profile_name, version_name=Latest):

        # Wipe existing data
        self._models["apps"].reset()
        self._models["context"].reset()
        self._models["environment"].reset()
        self._models["diagnose"].reset()
        self._models["packages"].reset()
        self._models["profileVersions"].setStringList([])

        self._state["rezContexts"].clear()
        self._state["rezEnvirons"].clear()
        self._state["testedEnvirons"].clear()
        self._state["rezApps"].clear()

        def on_apps_found(apps):
            if not apps:
                self._state["error"] = """
                <h2><font color=\"red\">:(</font></h2>
                <br>
                <br>
                The profile was found, but no applications.
                <br>
                <br>
                The profile didn't specify an application for you to use.<br>
                This is likely due to a misconfigured profile. Don't forget<br>
                to provide one or more packages as <i>weak references</i>.
                <br>
                <br>
                See <a href=https://allzpark.com/getting-started>
                    allzpark.com/getting-started</a> for more details.

                """
                self._state.to_noapps()

            else:
                self._models["apps"].reset(apps)
                self._state.to_ready()

        def on_apps_not_found(error, trace):
            # Handled by on_unhandled_exception
            raise error

        try:
            profile_versions = self._state["rezProfiles"][profile_name]
            active_profile = profile_versions[version_name]

        except KeyError:
            # This can only happen if somehow the view decided to pass
            # along the name and version of a profile that didn't exist.
            profile_name = self._state["profileName"]
            profile_versions = self._state["rezProfiles"][profile_name]
            active_profile = profile_versions[version_name]

            if profile_name:
                self.warning("%s was not found" % profile_name)
            else:
                self.error("select_profile was passed an empty string")

        refreshed = self._state["profileName"] == profile_name

        # TODO: This isn't clear.
        # We can't pass a native Rez Version object, but we also can't
        # simply str() that and BrokenPackage.version, as those would
        # be None, which is the equivalent of a NoVersion object.
        version_name = active_profile.version
        version_name = str(version_name) if version_name else NoVersion

        self._state["profileName"] = profile_name
        self.profile_changed.emit(
            profile_name,
            version_name,
            refreshed
        )

        if isinstance(active_profile, model.BrokenPackage):
            raise rez.PackageNotFoundError(
                "package not found: %s" % profile_name
            )

        # Update versions model
        versions = list(filter(None, profile_versions))  # Exclude "Latest"
        versions.reverse()  # Latest first
        self._models["profileVersions"].setStringList(versions)

        self._state.to_loading()
        util.defer(
            self._list_apps,
            args=[active_profile],
            on_success=on_apps_found,
            on_failure=on_apps_not_found,
        )

    def select_application(self, app_request):
        self._state["appRequest"] = app_request

        try:
            context = self.context(app_request)
            environ = self.environ(app_request)
            packages = self.resolved_packages(app_request)
            diagnose = self._state["testedEnvirons"].get(app_request, {})

        except Exception:
            self._models["packages"].reset()
            self._models["context"].reset()
            self._models["environment"].reset()
            self._models["diagnose"].reset()
            raise

        self._models["packages"].reset(packages)
        self._models["context"].load(context)
        self._models["environment"].load(environ)
        self._models["diagnose"].load(diagnose)

        tools = self._models["apps"].find(app_request)["tools"]
        self._state["tool"] = tools[0]

        # Use this application on next launch or change of profile
        self.update_command()
        self._state.store("startupApplication", app_request)
        self.application_changed.emit()

    def select_tool(self, tool_name):
        self._state["tool"] = tool_name
        self.update_command()

    def _package_paths(self):
        """Return all package paths, relative the current state of the world"""

        paths = rez.config.packages_path[:]

        # Optional development packages
        if not self._state.retrieve("useDevelopmentPackages"):
            paths = rez.config.nonlocal_packages_path[:]

        # Optional package localisation
        if localz and not self._state.retrieve("useLocalizedPackages", True):
            path = localz.localized_packages_path()

            try:
                paths.remove(util.normpath(path))
            except ValueError:
                # It may not be part of the path
                pass

        return paths

    def _list_apps(self, profile):
        # Each app has a unique context relative the current profile
        # Find it, and keep track of it.

        apps = []
        _apps = allzparkconfig.applications

        if self._state.retrieve("showAllApps") and not _apps:
            self.warning("Requires allzparkconfig.applications")

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

                    self.warning("Could not show all apps, "
                                 "missing `allzparkconfig.applications`")

        if not apps:
            apps[:] = allzparkconfig.applications_from_package(profile)

        # Optional patch
        patch = self._state.retrieve("patch", "").split()
        package_filter = self._package_filter()

        contexts = odict()
        with util.timing() as t:
            for app_request in apps:
                app_request = rez.PackageRequest(app_request.strip("~"))
                app_package = rez.find_latest(app_request.name,
                                              range_=app_request.range)

                if package_filter.excludes(app_package):
                    continue

                variants = list(profile.iter_variants())
                variant = variants[0]

                if len(variants) > 1:
                    # Unsure of whether this is desirable. It would enable
                    # a profile per platform, or potentially other kinds
                    # of special-purpose situations. If you see this,
                    # and want this, submit an issue with your use case!
                    self.warning(
                        "Profiles with multiple variants are unsupported. "
                        "Using first found: %s" % variant
                    )

                app_request = "%s==%s" % (app_package.name,
                                          app_package.version)

                request = [variant.qualified_package_name, app_request]
                self.debug("Resolving request: %s" % " ".join(request))

                context = self.env(request)

                if context.success and patch:
                    self.debug("Patching request: %s" % " ".join(request))
                    request = context.get_patched_request(patch)
                    context = self.env(
                        request,
                        use_filter=self._state.retrieve(
                            "patchWithFilter", False
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
                rez_pkg = model.BrokenPackage(app_request)

                self.warning(
                    "Couldn't find a corresponding package for "
                    "application %s. This can happen if an application is "
                    "patched away, using the ^-operator."
                    % app_request
                )

            except TypeError:
                # resolved_packages was None, a sign that a context was broken
                rez_pkg = model.BrokenPackage(app_request)

                if rez_context.success:
                    self.warning(
                        "This shouldn't have happened, "
                        "I was expecting a broken context here. "
                        "Please report this to "
                        "https://github.com/mottosso/allzpark/issues/66"
                    )

                self.error(
                    "Context for '%s' had no resolved packages, this is "
                    "likely due to a version conflict and broken resolve. "
                    "Try graphing it." % app_request
                )

            self._state["rezApps"][app_request] = rez_pkg

        self.debug("Resolved all contexts in %.2f seconds" % t.duration)

        # Hide hidden
        visible_apps = []
        show_hidden = self._state.retrieve("showHiddenApps")
        for request, package in self._state["rezApps"].items():
            data = allzparkconfig.metadata_from_package(package)
            hidden = data.get("hidden", False)

            if hidden and not show_hidden:
                continue

            visible_apps += [package]

        self._state["rezContexts"] = contexts
        return visible_apps

    def graph(self):
        context = self._state["rezContexts"][self._state["appRequest"]]
        graph_str = context.graph(as_dot=True)

        tempdir = tempfile.mkdtemp()
        fname = os.path.join(tempdir, "graph.png")

        try:
            rez.save_graph(graph_str, fname)
            pixmap = QtGui.QPixmap(fname)

        except IOError:
            self.error("GraphViz not found")
            return QtGui.QPixmap()

        finally:
            # Don't need this no more
            shutil.rmtree(tempdir)

        return pixmap

    def shell_code(self):
        app_request = self._state["appRequest"]
        context = self._state["rezContexts"][app_request]
        parent_env = self.parent_environ()
        return context.get_shell_code(parent_environ=parent_env)

    def test_environment(self):
        app_request = self._state["appRequest"]

        command = (
            '%s -c "'
            'import os,sys,json;'
            'sys.stdout.write(json.dumps(os.environ.copy(),ensure_ascii=0))"'
        ) % sys.executable

        def load(message):
            try:
                env = json.loads(message)
            except json.JSONDecodeError:
                self.info(message)  # regular messages during resolve
            else:
                self._state["testedEnvirons"][app_request] = env
                self._models["diagnose"].load(env)

        self.launch(command=command, stdout=load)


class Command(QtCore.QObject):
    stdout = QtCore.Signal(str)
    stderr = QtCore.Signal(str)
    killed = QtCore.Signal()

    error = QtCore.Signal(Exception)

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

        self.overrides = overrides or {}  # unused
        self.disabled = disabled or {}  # unused
        self.environ = environ or {}

        self.context = context
        self.app = package
        self.popen = None
        self.detached = detached

        # `cmd` rather than `command`, to distinguish
        # between class and argument
        self.cmd = command

        self._running = False

        # Launching may take a moment, and there's no need
        # for the user to wait around for that to happen.
        thread = threading.Thread(target=self._execute)
        thread.daemon = True

        self.thread = thread

    @property
    def pid(self):
        if self.popen.poll is None:
            return self.popen.pid

    def execute(self):
        self.thread.start()

    def _execute(self):
        startupinfo = None
        no_console = hasattr(allzparkconfig, "__noconsole__")

        # Windows-only
        # Prevent additional windows from appearing when running
        # Allzpark without a console, e.g. via pythonw.exe.
        if no_console and hasattr(subprocess, "STARTUPINFO"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        kwargs = {
            "command": self.cmd,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "parent_environ": self.environ or None,
            "startupinfo": startupinfo
        }
        if rez.project == "rez":
            # bleeding-rez adds `universal_newlines=True` when spawning shell,
            # nerdvegas/rez doesn't.
            kwargs["universal_newlines"] = True

        if sys.version_info[:2] >= (3, 6):
            kwargs["encoding"] = allzparkconfig.subprocess_encoding()
            kwargs["errors"] = allzparkconfig.unicode_decode_error_handler()

        context = self.context

        try:
            self.popen = context.execute_shell(**kwargs)
        except Exception as e:
            return self.error.emit(e)

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
