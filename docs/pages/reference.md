Short bite-sized snippets of information. This builds on information provided in the [guides](../guides) chapter.

<br>

### allzparkconfig.py

Configure allzpark using the `allzparkconfig.py`, which it will look for in these three locations, first one found wins.

- Your home directory, e.g. `~/allzparkonfig.py`
- Passed via command-line, e.g. `allzpark --config-file path/to/allzparkconfig.py`
- Or the environment, `ALLZPARK_CONFIG_FILE=/full/path/to/allzparkconfig.py`

All available keys and their default values can be found here.

- [`allzparkconfig.py`](https://github.com/mottosso/allzpark/blob/master/allzpark/allzparkconfig.py)

And an example can be found here:

- [rez-for-projects](https://github.com/mottosso/rez-for-projects/blob/master/allzparkconfig.py)

<br>

### Styling

All of the Allzpark graphical user interface can be styled interactively using CSS.

Custom styles are stored on the local machine, and can be shared and saved with copy/paste over e.g. chat or email.

- See [`style.css`](https://github.com/mottosso/allzpark/blob/master/allzpark/resources/style.css) for examples and documentation

![](https://user-images.githubusercontent.com/2152766/61289704-e1c7b880-a7c1-11e9-94ba-20ef7a2ca6bc.gif)

<br>

### Naming Convention

Requests are split between `name<operator><version>`

- Where `<operator>` is e.g. `-` or `==` or `>=`
- And `<version>` is an alphanumeric string, e.g. `1.0` or `latest` or `2.b2`

**Example**

```bash
rez env my_package-1  # package `my_package`, version `1` or above
rez env my-package-1  # package `my`, version `package-1` or above
rez env my_package_1  # package `my_package_1`, latest version
rez env my_package==1  # package `my_package_1`, version `1` exactly
```

- See [wiki](https://github.com/mottosso/bleeding-rez/wiki/Basic-Concepts#package-requests) for details.

<br>

### Automatic Environment Variables

Every package part of a resolve is given a series of environment variables.

- `REZ_(PKG)_BASE`
- `REZ_(PKG)_ROOT`
- `REZ_(PKG)_VERSION`
- `REZ_(PKG)_MAJOR_VERSION`
- `REZ_(PKG)_MINOR_VERSION`
- `REZ_(PKG)_PATCH_VERSION`

You can reference these from other packages, using the `{env.NAME}` notation, where `env` refers to the system environment, prior to packages having an effect.

**Example**

```python
# package.py
name = "my_package"
version = "1.0"
requires = ["my_package-1.0"]

def commands():
    global env
    env["MY_VARIABLE"] = r"c:\path\{env.REZ_MY_PACKAGE_VERSION}\scripts"
```

- See [wiki](https://github.com/mottosso/bleeding-rez/wiki/Environment-Variables#context-environment-variables) for details.

<br>

### Platform Specific Packages

A package can target a given platform using "variants".

**my_package/package.py**

```python
name = "my_package"
version = "1.0"
build_command = False
variants = [
    ["platform-windows"],
    ["platform-linux"],
]
```

- **Requesting** this package on `windows` would result in a version specific to Windows, and likewise for Linux.
- **Building** of this package happens *twice*; once per "variant".

<br>

#### Building Per Platform

```bash
$ cd my_package
$ rez build
Building variant 0 (1/2)...
Invoking custom build system...
Building variant 0 (2/2)...
The following package conflicts occurred: (platform-linux <--!--> ~platform==windows)
```

Since you cannot build a Linux package from Windows, nor vice versa, you can specify which variant to build using the `--variants` argument.

```bash
$ rez build --variants 0
```

Where `0` indicates the 0th index in the `package.py:variants = []` list.

- See [wiki](https://github.com/mottosso/bleeding-rez/wiki/Variants) for details
- See `rez build --help` for details

<br>

#### Options

You can reference any package and version as a variant, but generally you'll only need the platform specific ones, which come defined in `rezconfig.py` per default.

**rezconfig.py**

```python
implicit_packages = [
    "~platform=={system.platform}",
    "~arch=={system.arch}",
    "~os=={system.os}",
]
```

- See `rez config implicit_packages` for available options along with their values.

```bash
rez config implicit_packages
- ~platform==windows
- ~arch==AMD64
- ~os==windows-10
```

<br>

### Multiple Application Versions

Applications such as Python, Autodesk Maya and Adobe Photoshop can get packaged in one of two ways.

1. `maya-2018.1.0` i.e. "Serial"
2. `maya2018-1.0` i.e. "Parallel"

Let's refer to these as "serial" and "parallel" respectively. Which should you use, and why?

<br>

#### Uniform

In this example, there is only one package "family" for the Autodesk Maya software, whereby every revision of Maya is released as a new Rez package version; including "service packs" and "hotfixes" etc.

The advantage is that a package can then create a requirement on a range of `maya` versions.

```python
name = "mgear"
version = "1.0.0"
requires = ["maya>=2015,<2020"]
```

The disadvantage however is that you cannot resolve an environment with both `maya-2018` and `maya-2019`, as one would conflict with the other. Furthermore, if you did *force* this resolve, what should you expect to have happen in a situation like this?

```bash
$ rez env python-2 python-3
> $ python --version
Python ?.?.?
```

<br>

#### Parallel

Conversely, you can perform a "parallel" version.

**maya2018/package.py**

```python
name = "maya2018"
version = "1.0"
```

**maya2019/package.py**

```python
name = "maya2019"
version = "1.0"
```

In which case you are able to resolve an environment like this.

```bash
$ rez env maya2018 maya2019-1.0
> $
```

To work around the aforementioned issue of knowing which `python` - or in this case `maya` - is actually called, you can use an `alias()`.

**maya2019/package.py**

```python
name = "maya2019"
version = "1.0"

def commands():
    global alias
    alias("maya2019", "{root}/bin/maya.exe")
```

At which point you can call..

```bash
$ rez env maya2018 maya2019
> $ maya2018
# Launching Maya 2018..
```

However it isn't clear how you can make a requirement on a range of Maya versions with a parallel package. Consider the `mgear` package.

**mgear/package.py**

```python
name = "mgear"
version = "1.0"
requires = ["maya2018-1.0"]  # What about Maya 2019? :(
```

Rez [currently does not support](https://github.com/mottosso/bleeding-rez/issues/37) optional or "any"-style packages and so this approach would not be well suited for these types of requirements.

<br>

### Packages and Version Control

> Work in progress

If you got this far, and know more or want more, feel free to submit [an issue](https://github.com/mottosso/allzpark/issues).

<br>

### Release with GitLab

Once you've created a package, it's often a good idea to version control it.

```powershell
mkdir my_package
cd my_package
echo "name = `"my_package`"" >> package.py
echo "version = `"1.0.0`"" >> package.py
echo "build_command = False" >> package.py
git init
git add --all
git commit -m "Initial version"
git remote add-url https://gitlab.mycompany.com/username/my_package.git
git push
```

Next we'll configure GitLab to release a package alongside a new tag being made.

**.gitlab-ci.yml**

```yml
release:
  environment:
    - REZ_CONFIG_FILE=/packages/rezconfig.py
  script:
    - rez build --release
  only:
    - tags
```

> Work in progress

If you got this far, and know more or want more, feel free to submit [an issue](https://github.com/mottosso/allzpark/issues).

<br>

### Multiple Packages in a Single Git Repository

Sometimes, dedicating a Git repository or GitLab project for every package is too heavy-handed. Sometimes you have many small packages that all need version control, but not necessarily independently, such as project packages.

In this example, we'll create a Git repository containing 3 projects.

- Alita
- Spiderman
- Hulk

These projects are all released as individual Rez packages, but are managed in one Git repository.

```bash
mkdir my_projects
cd my_projects
mkdir alita
mkdir spiderman
mkdir hulk
```

Create a `package.py` in each project subdirectory, with something along the lines of:

```py
name = "alita"
version = "1.0.0"
build_command = False
```

Now we can commit and push these to, for example, your locally hosted GitLab instance.

```bash
git init
git add --all
git commit -m "Initial version"
git remote add-url https://gitlab.mycompany.com/username/my_projects.git
git push
```

When it's time to release, simply `cd` into a package of interest, and `--release`.

```bash
cd alita
rez build --install --release --clean
```

<br>

### Render on Farm

Typically, a context is resolved locally and work performed therein, and then further computation is submitted to a remote destination, such as a "render farm" or distributed compute network. In this case, it can be necessary to replicate a context remotely, in exactly the same configuration as locally.

But, you cannot assume:

1. Where packages are stored, because a remote computer may have different mount points
2. What OS the remote destination is running, because it may be e.g. Windows or Linux

<br>

#### Raw Environment

Because of the above, simply saving the environment as-is and restoring it elsewhere is rarely enough.

```python
import os
import json

# Not enough..
with open("environment.json", "w") as f:
    json.dump(f, dict(os.environ))
```

<br>

#### RXT

You may consider storing the resolved context to a file, for example..

```bash
rez env packageA packageB --output context.rxt  # Machine A
rez env --input context.rxt                     # Machine B
```

Alternatively..

```bash
rez env packageA packageB
> Get-Content $env:REZ_RXT_FILE > context.rxt
> exit
rez env --input context.rxt
```

But an exported context embeds *absolute paths* to where packages can be found, which may not be true on the remote end - such as a local render farm or remote cloud.

<br>

#### REZ_USED_RESOLVE

In this case, you may consider exporting the exact request, like this.

```bash
rez env packageA packageB --exclude *.beta
> $env:REZ_USED_RESOLVE
# packageA-2.33.3 packageB-5.12.3
```

However this may not be precise enough. The `-` indicator locks the included parts of a version, such as `5.12.3`, but doesn't exclude the possibility of a `5.12.3.beta` package, which takes precendence over `5.12.3`.

```bash
rez env packageA-2.33.3 packageB-5.12.3
> $env:REZ_USED_RESOLVE
# packageA-2.33.3 packageB-5.12.3.beta
```

> Notice the `.beta` towards the end.

Here's another example.

```bash
rez env packageA             # packageA-1.0.0.beta
rez env packageA-1.0.0       # packageA-1.0.0.beta
rez env packageA-1.0.0.beta  # packageA-1.0.0.beta
```

For that reason, passing `REZ_USED_RESOLVE` to `rez env` may not be enough to accurately reproduce a given environment.

<br>

#### Inherit Filter

So then what you could do, is pass along whatever filer you used to the remote end.

**Local**

```bash
rez env packageA packageB --exclude *.beta -- echo $env:REZ_USED_RESOLVE
# packageA-2.33.3 packageB-5.12.3
```

**Remote**

```bash
rez env packageA-2.33.3 packageB-5.12.3 --exclude *.beta
```

And presto, an identical environment.. but wait! What about `--patch`ed environments.

```bash
rez env packageA packageB --exclude *.beta
> rez env packageB-5.12.3.beta
>> $env:REZ_USED_RESOLVE
# packageA-2.33.3 packageB-5.12.3.beta
```

Now the final "used resolve" is incompatible with this filter, as `--exclude *.beta` would hide the beta version of `packageB`, resulting in..

```bash
12:18:12 ERROR    PackageNotFoundError: Package could not be found: packageB==5.12.3.beta
```

<br>

#### resolved_packages

So what is the solution? In a nutshell..

1. Resolve a context
2. Serialise `ResolvedContext.resolved_packages` to `{name}=={version}`

**used_resolve.py**

```python
from rez.status import status

# Use `status` to fetch an instance of ResolvedContext
# from within our current environment.
print(" ".join([
    "%s==%s" % (pkg.name, pkg.version)
    for pkg in status.context.resolved_packages
]))
```

Resulting in..

```bash
rez env python packageA packageB --exclude *.beta -- python used_resolve.py
# packageA==2.33.3 packageB==5.12.3
```

And presto, an accurate depiction of a given context, suitable for use again on the same machine, on a local render farm or remote cloud rendering environment.

<br>

#### requested_packages

What that last method _doesn't_ do however is guarantee that one resolve to work across platforms.

Take this package for example.

```python
name = "processmanager"
variants = [
    ["platform-windows", "win32all"],
    ["platform-linux", "unix-process-tool"],
]
```

On Windows, this would result in a list of resolved packages including `win32all` which isn't available on Linux, thus making the resulting request invalid.

In this case, you could instead use the `resolved_packages` variable.

**used_request.py**

```python
from rez.status import status

# Use `status` to fetch an instance of ResolvedContext
# from within our current environment.
print(" ".join([
    "%s==%s" % (pkg.name, pkg.version)
    for pkg in status.context.requested_packages()
]))
```

*However* this has a number of gotchas as well. For example, if the request was `alita==1.1 maya==2018` you would expect the resulting resolve to be identical, no matter where or when it's called. It would even accommodate for the problem is Linux versus Windows variants. What it *wouldn't* do however is protect against later versions of indirectly required packages from getting picked up.

For example.

1. Artist launches Maya session with `rez env alita==1.1 maya==2018`,  resulting in `["packageA-1.1"]`
2. Shortly thereafter, Developer releases `package-1.2`
3. From the same Maya session, artist submits job to a remote computer
4. The remote computer re-runs `rez env alita==1.1 maya==2018` but this time gets `["package-1.2"]` instead, resulting in a different environment than what was provided for the artist.

One solution to this problem is including a time stamp. Alongside every resolve is a `REZ_USED_TIMESTAMP` environment variable which keeps track of when a request was resolved. If you include this in your re-resolve, you'll be more likely to get what was requested at that point in time elsewhere.

```bash
rez env alita==1.1 maya==2018 --time $env:REZ_USED_TIMESTAMP
```

And presto, a cross-platform reproducible request!

<br>

#### Conversation

As you can tell, there are many ways to skin this cat. The following is a conversation about the various pros and cons and what to look out for.

- [Slack Conversation](https://gist.github.com/mottosso/54451ac5dd50ffdc8ba3e309e55c2d71)

<br>

### Testing Packages

Like any software projects, you need good tests. Software packaged with Rez is no exception, and doesn't *necessarily* change how you normally approach test.

There are a few ways to exercise your package.

<br>

#### Local Build and Run

The most useful and common approach is to build and run your package locally.

```bash
cd my_package
rez build --install
```

This will install the package into your local `~/packages` directory, overridden by  `REZ_LOCAL_PACKAGES_PATH`. From there, you can test a package *as though* it was deployed globally, until it's ready for an audience.

```bash
rez build --install --release
```

This command on the other hand installs a package into `~/.rez`, overridden by `REZ_RELEASE_PACKAGES_PATH`.

<br>

#### Test on Release

The above is a good start, but it's still possible for bugs to make their way into a deployed package unless you have a solid test suite.

```bash
cd my_package
nosetests2
# Testing..
```

For a Python project, tests can be written as though Rez was not involved, using any relevant test framework. But having tests means nothing unless they are actually exercised, and that's when setting up a "release hook" can help maintain consistency.

> Work in progress

If you got this far, and know more or want more, feel free to submit [an issue](https://github.com/mottosso/allzpark/issues).

<br>

### Hidden Applications

Allzpark serves two audiences - artists and developers. Developers want more customisation and control than the average artists, such as having additional debug or testing applications made available.

To address both of these audiences, there is a toggle called "Show Hidden Apps" which enables the package author to expose application packages with `hidden=True`.

**maya_dev/package.py**

```python
name = "maya_dev"
version = "2018.0"
build_command = False

# This is it
_data = {
    "hidden": True,
}
```

Now when this application is associated with a project, it is hidden per default, unless..

![image](https://user-images.githubusercontent.com/2152766/61438446-638d2280-a937-11e9-8c77-7ddf18af455d.png)

<br>

### All Applications

Each project specifies what applications to make available to the artist and developer. But sometimes, you don't care about that and just want to run Application X in a particular project environment.

> Work in progress

If you got this far, and know more or want more, feel free to submit [an issue](https://github.com/mottosso/allzpark/issues).

<br>

### Opt-out Environment

Per default, the parent environment is inherited by a Rez context, unless one or more packages reference it internally.

```bash
$env:MY_PATH="path1;path2"
rez env
> $env:MY_PATH
# path1;path2
```

Note the inheritance there. However, if any package references `MY_PATH` then it will automatically clear itself prior to being re-added by the package.

**package.py**

```python
name = "my_package"
version = "1.0"

def commands():
    env["MY_PATH"].append("path1")  # Clearing existing PATH
```

If we include this package, the variable now looks like this.

```bash
rez env my_package
> $env:MY_PATH
# path1
```

This is considered a bug in the underlying bleeding-rez library, and is being addressed here.

- See also https://github.com/mottosso/bleeding-rez/issues/70

<br>

### Graph

Allzpark is able to visualise a resolved context as a graph.

![]()

**Prerequisities**

In order to enable graph drawing, you need the following package(s).

- `graphviz-2+`

**Usage**

To make Allzpark aware of `graphviz`, simply include it in your request prior to launching.

```powershell
rez env graphviz pyside2 python-3 bleeding_rez -- python -m allzpark
```

<br>

### Localisation

Users are able to interactively localize packages from the Packages tab, to save on performance or to work offline.

**Prerequisities**

In order to enable localization, you'll need the following package(s).

- `localz-1+`

**Usage**

Make Allzpark aware of `localz` by including it in your request.

```powershell
rez env localz pyside2 python3 bleeding_rez -- python -m allzpark
```

<br>

### Allzpark Performance Considerations

Use of the Allzpark can be divided into roughly three parts.

1. Time taken to load libraries such as PySide2 - you should be seeing timings in the console
    - Can be resolved by localizing packages, primarily python and PySide
2. Time taken to get the window open
    - Is actual building of the Allzpark and difficult to avoid
3. Time taken to when applications, like Maya, actually show up
    - This is the actual Rez resolves taking place. It will vary depending on whether the contexts can be found in memcached or not, which is about 90% of the time.

From there most things are stored in-memory and won't perform many if any IO or CPU intensive calls, with a few exceptions like generating the resolve graph in the Context tab.
