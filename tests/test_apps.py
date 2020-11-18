
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
        with self.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])
        self.wait(timeout=200)
        self.assertEqual(self.ctrl.state.state, "ready")

        with self.wait_signal(self.ctrl.state_changed, "ready"):
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
        with self.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])
        self.wait(timeout=200)
        self.assertEqual(self.ctrl.state.state, "ready")

        with self.wait_signal(self.ctrl.state_changed, "ready"):
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

    def test_app_failed_independently_1(self):
        """Test app resolve failure doesn't fail whole profile"""
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "anti_A",
                        "~app_A",  # fail by reduction
                        "~app_B",
                    ],
                },
            },
            "anti_A": {
                "1": {
                    "name": "anti_A",
                    "version": "1",
                    "requires": ["!app_A"],
                }
            },
            "app_A": {"1": {"name": "app_A", "version": "1"}},
            "app_B": {"1": {"name": "app_B", "version": "1"}},
        })
        with self.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])
        self.wait(timeout=200)
        self.assertEqual(self.ctrl.state.state, "ready")

        context_a = self.ctrl.state["rezContexts"]["app_A==1"]
        context_b = self.ctrl.state["rezContexts"]["app_B==1"]

        self.assertFalse(context_a.success)
        self.assertTrue(context_b.success)

    def test_app_failed_independently_2(self):
        """Test app missing doesn't fail whole profile"""
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "~app_A",  # missing package family
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

        self.assertFalse(context_a.success)  # broken context
        self.assertTrue(context_b.success)

    def test_app_failed_independently_3(self):
        """Test app missing dependency doesn't fail whole profile"""
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "~app_A",  # has missing requires
                        "~app_B",
                    ],
                },
            },
            "app_A": {
                "1": {
                    "name": "app_A",
                    "version": "1",
                    "requires": ["missing"],
                }
            },
            "app_B": {"1": {"name": "app_B", "version": "1"}},
        })
        with self.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])
        self.wait(timeout=200)
        self.assertEqual(self.ctrl.state.state, "ready")

        context_a = self.ctrl.state["rezContexts"]["app_A==1"]
        context_b = self.ctrl.state["rezContexts"]["app_B==1"]

        self.assertFalse(context_a.success)
        self.assertTrue(context_b.success)

    def test_app_failed_independently_4(self):
        """Test app missing version/variant doesn't fail whole profile"""
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "~app_A==2",  # missing package
                        "~app_B",
                    ],
                },
            },
            "app_A": {"1": {"name": "app_A", "version": "1"}},
            "app_B": {"1": {"name": "app_B", "version": "1"}},
        })
        with self.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])
        self.wait(timeout=200)
        self.assertEqual(self.ctrl.state.state, "ready")

        context_a = self.ctrl.state["rezContexts"]["app_A==2"]
        context_b = self.ctrl.state["rezContexts"]["app_B==1"]

        self.assertFalse(context_a.success)
        self.assertTrue(context_b.success)

    def test_app_exclusion_filter(self):
        """Test app is available when latest version matches rez
        exclusion filter
        """
        from allzpark import allzparkconfig

        self.assertEqual(allzparkconfig.exclude_filter, "*.beta")

        utils.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo":
                    "version": "1.0.0",
                    "requires": [
                        "~app-1"  # latest app_A version matches exclusion filter
                    ]
                }
            },
            "app_A": {
                "1.0.0": {
                    "name": "app_A",
                    "version": "1.0.0"
                },
                "1.0.0.beta": {
                    "name": "app_A",
                    "version": "1.0.0.beta"
                }
            }
        })
        with self.wait_signal(self.ctrl.resetted):
            self.ctrl.reset(["foo"])
        self.wait(timeout=200)
        self.assertEqual(self.ctrl.state.state, "ready")

        # App was added
        self.assertIn("appA-1", self.ctrl.state["rezContexts"])
        context_a = self.ctrl.state["rezContexts"]["appA-1"]
        self.assertTrue(context_a.success)

        # Latest non-beta version was chosen
        resolved_pkgs = [p for p in context_a.resolved_packages
                         if "appA" == p.name and "1.0.0" == str(p.version)]
        assert(resolved_pkgs)
