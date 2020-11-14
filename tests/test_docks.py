
from tests import util


class TestDocks(util.TestBase):

    def test_feature_blocked_on_failed_app(self):
        """Test feature blocked if application is broken"""
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "~app_A",  # missing package (broken app)
                        "~app_B",
                    ],
                },
            },
            "app_B": {"1": {"name": "app_B", "version": "1"}},
        })
        self.ctrl_reset(["foo"])

        self.set_preference("showAdvancedControls", True)

        context_a = self.ctrl.state["rezContexts"]["app_A==None"]
        context_b = self.ctrl.state["rezContexts"]["app_B==1"]

        self.assertFalse(context_a.success)
        self.assertTrue(context_b.success)

        for app, state in {"app_A==None": False, "app_B==1": True}.items():
            self.select_application(app)

            dock = self.show_dock("environment", on_page="diagnose")
            self.assertEqual(dock._widgets["compute"].isEnabled(), state)

            dock = self.show_dock("context", on_page="code")
            self.assertEqual(dock._widgets["printCode"].isEnabled(), state)

            dock = self.show_dock("app")
            self.assertEqual(dock._widgets["launchBtn"].isEnabled(), state)

    def test_version_editable_on_show_all_versions(self):
        """Test version is editable when show all version enabled"""
        self._test_version_editable(show_all_version=True)

    def test_version_editable_on_not_show_all_versions(self):
        """Test version is not editable when show all version disabled"""
        self._test_version_editable(show_all_version=False)

    def _test_version_editable(self, show_all_version):
        util.memory_repository({
            "foo": {
                "1": {"name": "foo", "version": "1",
                      "requires": ["~app_A", "~app_B"]},
                "2": {"name": "foo", "version": "2",
                      "requires": ["~app_A", "~app_B"]},
            },
            "app_A": {"1": {"name": "app_A", "version": "1"}},
            "app_B": {"1": {"name": "app_B", "version": "1",
                            "requires": ["bar"]}},
            "bar": {"1": {"name": "bar", "version": "1"},
                    "2": {"name": "bar", "version": "2"}}
        })
        self.ctrl_reset(["foo"])

        self.set_preference("showAdvancedControls", True)
        self.set_preference("showAllVersions", show_all_version)
        self.wait(200)  # wait for reset

        self.select_application("app_B==1")

        dock = self.show_dock("packages")
        view = dock._widgets["view"]
        proxy = view.model()
        model = proxy.sourceModel()

        for pkg, state in {"foo": False,  # profile can't change version here
                           "bar": show_all_version,
                           "app_B": False}.items():
            index = model.findIndex(pkg)
            index = proxy.mapFromSource(index)

            rect = view.visualRect(index)
            position = rect.center()
            with util.patch_cursor_pos(view.mapToGlobal(position)):
                dock.on_right_click(position)
                menu = self.get_menu(dock)
                edit_action = next((a for a in menu.actions()
                                    if a.text() == "Edit"), None)
                if edit_action is None:
                    self.fail("No version edit action.")

                self.assertEqual(
                    edit_action.isEnabled(), state,
                    "Package '%s' version edit state is incorrect." % pkg
                )

                self.wait(200)
                menu.close()
