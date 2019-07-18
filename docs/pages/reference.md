Short bite-sized snippets of information. This builds on information provided in the [guides](../guides) chapter.

<br>

### allzparkconfig.py

Configure allzpark using the `allzparkconfig.py`.

- `touch ~/allzparkconfig.py` Store in your `$HOME` directory
- `allzpark --config-file path/to/allzparkconfig.py` Or pass directly
- `ALLZPARK_CONFIG_FILE` Or pass via environment variable

All available keys and their default values can be found here.

- [`allzparkconfig.py`](https://github.com/mottosso/allzpark/blob/master/allzpark/allzparkconfig.py)

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
