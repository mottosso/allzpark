This page provides a transition guide from using Avalon's native Launcher to Allzpark.

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
rez env pipz -- install avalon colorbleed pyqt5==5.8 pymongo>=3.4
git clone https://github.com/mottosso/bleed.git
cd bleed
rez build --install
python -m avalon.inventory --save
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

### Core Differences

**Launcher**

- Has all the information related to a project, asset and task
- Creates working directory *prior* to application launch

Avalon provides an API for defining an application on disk.

```toml
application_dir = "maya"
default_dirs = [
    "scenes",
    "data",
    "renderData/shaders",
    "images",
    "renders"
]
label = "Autodesk Maya 2018"
schema = "avalon-core:application-1.0"
executable = "maya2018"
description = ""
icon = "cubes"
color = "#CCBD14"
order = -2

[copy]
"{COLORBLEED_CONFIG}/res/workspace.mel" = "workspace.mel"

[environment]
FFMPEG_PATH="P:/pipeline/dev/apps/ffmpeg/bin/ffmpeg.exe"

COLORBLEED_SCRIPTS="P:/pipeline/dev/git/cbMayaScripts/cbMayaScripts"

MAYA_DISABLE_CLIC_IPM = "Yes"  # Disable the AdSSO process
MAYA_DISABLE_CIP = "Yes"  # Shorten time to boot
MAYA_DISABLE_CER = "Yes"
PYMEL_SKIP_MEL_INIT = "Yes"
LC_ALL= "C"  # Mute color management warnings
REDSHIFT_DISABLEOUTPUTLOCKFILES = "1" # Disable Redshift creating lock files

XBMLANGPATH = [
    "P:/pipeline/dev/apps/maya_shared/2018/prefs/icons"
]

MAYA_SCRIPT_PATH = [
    "P:/pipeline/dev/apps/maya_shared/2018/scripts"
]

# Fix V-ray forcing affinity to 100%
VRAY_USE_THREAD_AFFINITY = "0"

PYTHONPATH = [
    "P:/pipeline/dev/git/Qt.py",
    "P:/pipeline/dev/apps/maya_shared/2018/modules/cvshapeinverter",
    "{AVALON_CORE}/setup/maya",
    "{PYTHONPATH}"
]

MAYA_MODULE_PATH = [
    "P:/pipeline/dev/apps/maya_shared/2018/modules/Yeti-v3.1.9_Maya2018-windows",
    "P:/pipeline/dev/apps/maya_shared/2018/modules/cvshapeinverter",
    "P:/pipeline/dev/apps/maya_shared/2018/modules/brSmoothWeights",
    "P:/pipeline/dev/apps/maya_shared/2018/modules/SHAPES"
]
PATH = [
    "P:/pipeline/dev/apps/maya_shared/2018/modules/Yeti-v3.1.9_Maya2018-windows/bin",
    "{PATH}"
]

```

It then let's you reference this definition using its unique identifier, such as `maya` or `nuke`.