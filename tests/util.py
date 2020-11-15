
import os
import time
import unittest
import contextlib


MEMORY_LOCATION = "memory@any"


def memory_repository(packages):
    from rezplugins.package_repository import memory
    from allzpark import _rezapi as rez

    class MemoryVariantRes(memory.MemoryVariantResource):
        def _root(self):  # implement `root` to work with localz
            return MEMORY_LOCATION

    manager = rez.package_repository_manager
    repository = manager.get_repository(MEMORY_LOCATION)
    repository.pool.resource_classes[MemoryVariantRes.key] = MemoryVariantRes
    repository.data = packages


class TestBase(unittest.TestCase):

    def setUp(self):
        from allzpark import cli

        os.environ["ALLZPARK_PREFERENCES_NAME"] = "preferences_test"
        os.environ["REZ_PACKAGES_PATH"] = MEMORY_LOCATION

        app, ctrl = cli.initialize(clean=True, verbose=3)
        window = cli.launch(ctrl)

        size = window.size()
        window.resize(size.width() + 80, size.height() + 80)

        self.app = app
        self.ctrl = ctrl
        self.window = window
        self.patched_allzparkconfig = dict()

        self.wait(timeout=50)

    def tearDown(self):
        self.wait(timeout=500)
        self.window.close()
        self.ctrl.deleteLater()
        self.window.deleteLater()
        self._restore_allzparkconfig()
        time.sleep(0.1)

    def _restore_allzparkconfig(self):
        from allzpark import allzparkconfig

        for name, value in self.patched_allzparkconfig.items():
            setattr(allzparkconfig, name, value)

        self.patched_allzparkconfig.clear()

    def patch_allzparkconfig(self, name, value):
        from allzpark import allzparkconfig

        if name not in self.patched_allzparkconfig:
            original = getattr(allzparkconfig, name)
            self.patched_allzparkconfig[name] = original

        setattr(allzparkconfig, name, value)

    def set_preference(self, name, value):
        preferences = self.window._docks["preferences"]
        arg = next((opt for opt in preferences.options
                    if opt["name"] == name), None)
        if not arg:
            self.fail("Preference doesn't have this setting: %s" % name)

        try:
            arg.write(value)
        except Exception as e:
            self.fail("Preference '%s' set failed: %s" % (name, str(e)))

    def show_dock(self, name, on_page=None):
        dock = self.window._docks[name]
        dock.toggle.setChecked(True)
        dock.toggle.clicked.emit()
        self.wait(timeout=50)

        if on_page is not None:
            tabs = dock._panels["central"]
            page = dock._pages[on_page]
            index = tabs.indexOf(page)
            tabs.tabBar().setCurrentIndex(index)

        return dock

    def ctrl_reset(self, profiles):
        with self.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(profiles)
        self.wait(timeout=200)
        self.assertEqual(self.ctrl.state.state, "ready")

    def select_application(self, app_request):
        apps = self.window._widgets["apps"]
        proxy = apps.model()
        model = proxy.sourceModel()
        index = model.findIndex(app_request)
        index = proxy.mapFromSource(index)

        sel_model = apps.selectionModel()
        sel_model.select(index, sel_model.ClearAndSelect | sel_model.Rows)
        self.wait(50)

    def wait(self, timeout=1000):
        from allzpark.vendor.Qt import QtCore

        loop = QtCore.QEventLoop(self.window)
        timer = QtCore.QTimer(self.window)

        def on_timeout():
            timer.stop()
            loop.quit()

        timer.timeout.connect(on_timeout)
        timer.start(timeout)
        loop.exec_()

    @contextlib.contextmanager
    def wait_signal(self, signal, on_value=None, timeout=1000):
        from allzpark.vendor.Qt import QtCore

        loop = QtCore.QEventLoop(self.window)
        timer = QtCore.QTimer(self.window)
        state = {"received": False}

        if on_value is None:
            def trigger(*args):
                state["received"] = True
                timer.stop()
                loop.quit()
        else:
            def trigger(value):
                if value == on_value:
                    state["received"] = True
                    timer.stop()
                    loop.quit()

        def on_timeout():
            timer.stop()
            loop.quit()
            self.fail("Signal waiting timeout.")

        signal.connect(trigger)
        timer.timeout.connect(on_timeout)

        try:
            yield
        finally:
            if not state["received"]:
                timer.start(timeout)
                loop.exec_()

    def get_menu(self, widget):
        from allzpark.vendor.Qt import QtWidgets
        menus = widget.findChildren(QtWidgets.QMenu, "")
        menu = next((m for m in menus if m.isVisible()), None)
        if menu:
            return menu
        else:
            self.fail("This widget doesn't have menu.")


@contextlib.contextmanager
def patch_cursor_pos(point):
    from allzpark.vendor.Qt import QtGui

    origin_pos = getattr(QtGui.QCursor, "pos")
    setattr(QtGui.QCursor, "pos", lambda: point)
    try:
        yield
    finally:
        setattr(QtGui.QCursor, "pos", origin_pos)
