
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
        with self.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])
        self.wait(timeout=200)
        self.assertEqual(self.ctrl.state.state, "ready")

        context_a = self.ctrl.state["rezContexts"]["app_A==None"]
        context_b = self.ctrl.state["rezContexts"]["app_B==1"]

        self.assertFalse(context_a.success)
        self.assertTrue(context_b.success)

        self.show_advance_controls()

        for app, state in {"app_A==None": False, "app_B==1": True}.items():
            self.ctrl.select_application(app)
            self.wait(100)

            dock = self.show_dock("environment", on_page="diagnose")
            self.assertEqual(dock._widgets["compute"].isEnabled(), state)

            dock = self.show_dock("context", on_page="code")
            self.assertEqual(dock._widgets["printCode"].isEnabled(), state)

            dock = self.show_dock("app")
            self.assertEqual(dock._widgets["launchBtn"].isEnabled(), state)
