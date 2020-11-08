
from tests import util


class TestApps(util.TestBase):

    def test_select_app(self):
        """Test app selecting behavior
        """
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "~app_A",
                        "~app_B",
                    ],
                }
            },
            "app_A": {
                "1.0.0": {
                    "name": "app_A",
                    "version": "1.0.0",
                }
            },
            "app_B": {
                "1.0.0": {
                    "name": "app_B",
                    "version": "1.0.0",
                }
            },
        })
        with util.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])

        with util.wait_signal(self.ctrl.state_changed, "ready"):
            self.ctrl.select_profile("foo")

        env = self.ctrl.state["rezEnvirons"]

        # first app will be selected if no preference loaded
        self.assertEqual("app_A==1.0.0", self.ctrl.state["appRequest"])
        self.assertIn("app_A==1.0.0", env)
        self.assertNotIn("app_B==1.0.0", env)

        self.ctrl.select_application("app_B==1.0.0")

        self.assertEqual("app_B==1.0.0", self.ctrl.state["appRequest"])
        self.assertIn("app_A==1.0.0", env)
        self.assertIn("app_B==1.0.0", env)

    def test_app_environ(self):
        """Test resolved environment in each app
        """
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "~app_A",
                        "~app_B",
                    ],
                    "commands": "env.FOO='BAR'"
                }
            },
            "app_A": {
                "1.0.0": {
                    "name": "app_A",
                    "version": "1.0.0",
                    "commands": "env.THIS_A='1'"
                }
            },
            "app_B": {
                "1.0.0": {
                    "name": "app_B",
                    "version": "1.0.0",
                    "commands": "env.THIS_B='1'"
                }
            },
        })
        with util.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])

        with util.wait_signal(self.ctrl.state_changed, "ready"):
            self.ctrl.select_profile("foo")

        env = self.ctrl.state["rezEnvirons"]

        for app_request in ["app_A==1.0.0", "app_B==1.0.0"]:
            self.ctrl.select_application(app_request)

        self.assertIn("app_A==1.0.0", env)
        self.assertIn("app_B==1.0.0", env)

        # profile env will apply to all apps
        self.assertIn("FOO", env["app_A==1.0.0"])
        self.assertIn("FOO", env["app_B==1.0.0"])
        self.assertEqual(env["app_A==1.0.0"]["FOO"], "BAR")
        self.assertEqual(env["app_B==1.0.0"]["FOO"], "BAR")

        self.assertIn("THIS_A", env["app_A==1.0.0"])
        self.assertNotIn("THIS_A", env["app_B==1.0.0"])

        self.assertIn("THIS_B", env["app_B==1.0.0"])
        self.assertNotIn("THIS_B", env["app_A==1.0.0"])
