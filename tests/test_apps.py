
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
        self.ctrl_reset(["foo"])

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
        self.ctrl_reset(["foo"])

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
        self.ctrl_reset(["foo"])

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
        self.ctrl_reset(["foo"])

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
        self.ctrl_reset(["foo"])

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
        self.ctrl_reset(["foo"])

        context_a = self.ctrl.state["rezContexts"]["app_A==2"]
        context_b = self.ctrl.state["rezContexts"]["app_B==1"]

        self.assertFalse(context_a.success)
        self.assertTrue(context_b.success)

    def test_app_changing_version(self):
        """Test application version can be changed in view"""
        util.memory_repository({
            "foo": {
                "1": {"name": "foo", "version": "1",
                      "requires": ["~app_A", "~app_B"]}
            },
            "app_A": {"1": {"name": "app_A", "version": "1"}},
            "app_B": {"1": {"name": "app_B", "version": "1"},
                      "2": {"name": "app_B", "version": "2"}}
        })
        self.ctrl_reset(["foo"])
        self.show_dock("app")

        apps = self.window._widgets["apps"]

        def get_version_editor(app_request):
            self.select_application(app_request)
            proxy = apps.model()
            model = proxy.sourceModel()
            index = model.findIndex(app_request, column=1)
            index = proxy.mapFromSource(index)
            apps.edit(index)

            return apps.indexWidget(index), apps.itemDelegate(index)

        editor, delegate = get_version_editor("app_A==1")
        self.assertIsNone(
            editor, "No version editing if App has only one version.")

        editor, delegate = get_version_editor("app_B==2")
        self.assertIsNotNone(
            editor, "Version should be editable if App has versions.")

        # for visual
        editor.showPopup()
        self.wait(100)
        view = editor.view()
        index = view.model().index(0, 0)
        sel_model = view.selectionModel()
        sel_model.select(index, sel_model.ClearAndSelect)
        self.wait(150)
        # change version
        editor.setCurrentIndex(0)
        delegate.commitData.emit(editor)
        self.wait(200)  # wait patch

        self.assertEqual("app_B==1", self.ctrl.state["appRequest"])

    def test_app_no_version_change_if_flattened(self):
        """No version edit if versions are flattened with allzparkconfig"""

        def applications_from_package(variant):
            # From https://allzpark.com/gui/#multiple-application-versions
            from allzpark import _rezapi as rez

            requirements = variant.requires or []
            apps = list(
                str(req)
                for req in requirements
                if req.weak
            )
            apps = [rez.PackageRequest(req.strip("~")) for req in apps]
            flattened = list()
            for request in apps:
                flattened += rez.find(
                    request.name,
                    range_=request.range,
                )
            apps = list(
                "%s==%s" % (package.name, package.version)
                for package in flattened
            )
            return apps

        # patch config
        self.patch_allzparkconfig("applications_from_package",
                                  applications_from_package)
        # start
        util.memory_repository({
            "foo": {
                "1": {"name": "foo", "version": "1",
                      "requires": ["~app_A"]}
            },
            "app_A": {"1": {"name": "app_A", "version": "1"},
                      "2": {"name": "app_A", "version": "2"}}
        })
        self.ctrl_reset(["foo"])
        self.show_dock("app")

        apps = self.window._widgets["apps"]

        def get_version_editor(app_request):
            self.select_application(app_request)
            proxy = apps.model()
            model = proxy.sourceModel()
            index = model.findIndex(app_request, column=1)
            index = proxy.mapFromSource(index)
            apps.edit(index)

            return apps.indexWidget(index), apps.itemDelegate(index)

        editor, delegate = get_version_editor("app_A==1")
        self.assertIsNone(
            editor, "No version editing if versions are flattened.")

        editor, delegate = get_version_editor("app_A==2")
        self.assertIsNone(
            editor, "No version editing if versions are flattened.")

    def test_app_exclusion_filter(self):
        """Test app is available when latest version excluded by filter"""
        util.memory_repository({
            "foo": {
                "1.0.0": {
                    "name": "foo",
                    "version": "1.0.0",
                    "requires": [
                        "~app_A-1"
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
                    # latest app_A version matches exclusion filter
                }
            }
        })
        self.ctrl_reset(["foo"])

        self.set_preference("exclusionFilter", "*.beta")
        self.wait(200)  # wait for reset

        # App was added
        self.assertIn("app_A==1.0.0", self.ctrl.state["rezContexts"])
        context_a = self.ctrl.state["rezContexts"]["app_A==1.0.0"]
        self.assertTrue(context_a.success)

        # Latest non-beta version was chosen
        resolved_pkgs = [p for p in context_a.resolved_packages
                         if "app_A" == p.name and "1.0.0" == str(p.version)]
        self.assertEqual(1, len(resolved_pkgs))
