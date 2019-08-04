This page provides a transition guide from using [Avalon](https://getavalon.github.io)'s native Launcher to Allzpark.

<br>

### Quickstart

This part assumes a successful [Quickstart](/quickstart).

<div class="tabs">
  <button class="tab powershell " onclick="setTab(event, 'powershell')"><p>powershell</p><div class="tab-gap"></div></button>
  <button class="tab bash " onclick="setTab(event, 'bash')"><p>bash</p><div class="tab-gap"></div></button>
</div>

<div class="tab-content powershell" markdown="1">

```powershell
mkdir $env:USERPROFILE/projects
substr P: $env:USERPROFILE/projects
$env:REZ_PACKAGES_PATH="~/packages;$(allzparkdemo --packages)"
$env:MY_PROFILES="bleed"
```

</div>

<div class="tab-content bash" markdown="1">

```bash
mkdir ~/projects
$REZ_PACKAGES_PATH=~/packages:$(allzparkdemo --packages)
$MY_PROFILES=bleed
```

</div>

```bash
# Convert PyPI packages to Rez
git clone https://github.com/mottosso/rez-pipz.git
cd rez-pipz
rez build --install
cd ..

# Install PyPI dependencies
rez env pipz -- install avalon-core avalon-colorbleed pymongo>=3.4

# Install Avalon demo project
git clone https://github.com/mottosso/bleed.git
cd bleed
rez build --install
python -m avalon.inventory --save

# Launch!
allzpark --demo
```

??? question "`~/projects`"
    For the purposes of this demo, the Avalon projects are assumed to be in this directory.

??? question "pipz"
    These are the base requirements for running Avalon

??? question "REZ_PACKAGES_PATH"
    For the purposes of this demo, we'll expose the Allzpark demo packages, primarily `maya`, `blender` and `rezutil` for use when building `bleed`. We could also have made a `maya`, `blender` and `rezutil` package globally, and skipped this step.

??? question "avalon.inventory"
    We'll also need this project uploaded to Avalon's MongoDB database. I'd like to skip this step, to instead automatically create projects post-launch, based on variables set in the Allzpark profile.

<br>

### Bleed Profile

Let's have a look at how `bleed` is laid out.

- [bleed/package.py](https://github.com/mottosso/bleed/blob/master/package.py)

```py
name = "bleed"
version = "1.0.15"
build_command = "python -m rezutil build {root}"
private_build_requires = ["rezutil-1"]
```

Nothing special here; we're building on the `rezutil` package from the Allzpark demo library to simplify the installation somewhat, it handles copying of the contained `userSetup.py`.

```py
_requires = [
    "~blender==2.80.0",
    "~maya==2015.0.0|2016.0.2|2017.0.4|2018.0.6",

    "pymongo-3.4+",

    "avalon_core-5.2+",
    "avalon_colorbleed-1",
]
```

Again we're referencing `blender` and `maya` from the demo library, in this case a number of versions of Maya to cover all bases. Allzpark displays every version that matches this pattern, in this case 4 versions of Maya.

`pymongo` is the only real dependency to Avalon, the others being vendored, due to being the only one that isn't a pure-Python library. Finally, Avalon core and the colorbleed config is added are requirements to this profile.

```py
@late()
def requires():
    global this
    global request
    global in_context

    requires = this._requires

    # Add request-specific requirements
    if in_context():
        if "maya" in request:
            requires += [
                "mgear",
            ]

    return requires
```

You'll notices the previous `_requires = []` had an underscore in it, which makes it invisible to Rez. Instead, we use this function `requires()` with a `@late()` decorator which makes Rez compute the requirements of this package when called, as opposed to when built.

If called during built, the previously specified requirements are included. However, when called the `in_context()` function evaluates to `True` which in turn queries the request we made, e.g. `rez env bleed maya`, for whether "maya" was included. If so, then it goes ahead and appends `mgear` as another requirement for this profile.

This is how you can specifiy *conditional* requirements for a given profile, requirements that come into effect only when used in combination with a particular set of requirements, like `maya`. In this case, `mgear` is only relevant to Maya, and not Blender.

```py
def commands():
    import os
    import tempfile

    global env
    global this
    global request

    # Better suited for a global/studio package
    projects = r"p:\projects" if os.name == "nt" else "~/projects"

    env["AVALON_PROJECTS"] = projects
    env["AVALON_CONFIG"] = "colorbleed"
    env["AVALON_PROJECT"] = this.name
    env["AVALON_EARLY_ADOPTER"] = "yes"
```

Next we give configure Allzpark with the necessary environment variables.

- `AVALON_PROJECTS` is typically a global value for your studio, and better suited for a package required by every profile, like a `global` or `studio` package. I've included it here to keep the example self-contained.
- `AVALON_CONFIG` here we reference the `avalon_colorbleed` requirement
- `AVALON_PROJECT` storing the project name into the environment, referencing the `this` variable, which is the equivalent of `self` from within a class; it references the members from outside of the `commands()` function, in this case the `name` of the package itself; "bleed"
- `AVALON_EARLY_ADOPTER` finally enabling some of the later features of Avalon

```py
if "maya" in request:
    env["PYTHONPATH"].append("{root}/maya")  # userSetup.py
```

Another conditional event; the `bleed` package includes a folder of profile-specific Maya scripts that are added to `PYTHONPATH` only if `maya` is part of the request.

```py
env["AVALON_TASK"] = "modeling"
env["AVALON_ASSET"] = "hero"
env["AVALON_SILO"] = "asset"
env["AVALON_WORKDIR"] = tempfile.gettempdir()
```

Finally, the members that we need to get rid of from the application launching process of Avalon; these need to happen post-launch.

<br>

### Differences

Overall, Allzpark and Launcher are very similar.

- **All Knowing** Launcher has all the information related to a project, asset and task
    - We'll need to split this responsibility and let Allzpark handle anything related to application startup, but leave assets and tasks to Avalon
- **Working Directory** Launcher is responsible for creating a working directory, *prior* to application launch
    - Because is knows all of these things, it's a good fit for creating the initial working directory wherein an application saves data, like Maya's `workspace.mel` file and associated hierarchy. Because Allzpark isn't concerned with such things, we'll need to let the host deal with this.
    - An upside of this is that artists would then be able to switch task/asset/shot without a restart

<br>

### Todo

- [ ] **DB** Create Avalon MongoDB project document post-launch
- [ ] **Working Directory** Create working directory post-launch
    - E.g. via "Set Context"
- [x] Create new assets interactively, rather than from .toml
    - I.e. launch "Project Manager" from Allzpark

The above example works, but embeds too much information into the Allzpark profile, notably these:

```py
env["AVALON_TASK"] = "modeling"
env["AVALON_ASSET"] = "hero"
env["AVALON_SILO"] = "asset"
env["AVALON_WORKDIR"] = tempfile.gettempdir()
```
