Learn Allzpark by example. This assumes you've already accumulated the knowledge from the [guides](../guides) chapter.

<br>

## Examples

This page contains a series of solutions to specific problems.

<br>

### Command Shorthand

<img width=381 src=https://user-images.githubusercontent.com/2152766/60725113-2e90d100-9f30-11e9-9fe5-866e7038a3fa.png></h3>

Use `rez env` to establish a context, and `--command` to immediately run a command within that context.

```powershell
rez env --command="echo Hello"
```

Instead of using `--command`, you can also use `--`.

```powershell
rez env -- echo Hello
```

Note that you didn't need quotation marks or an `=` sign for this to work, and that it's a little easier on the eyes. We use this syntax extensively throughout this guide.

<br>

## External Packages

With Rez you can package almost anything, but sometimes there are packages already made for you to benefit from.

<br>

### Install from PyPI

Managing external projects is no fun unless you can benefit from what package authors in neighboring ecosystems have been working on. PyPI is such an ecosystem and you can install any package from PyPI as a Rez package using `rez-pipz`.

```bash
git clone https://github.com/mottosso/rez-pipz.git
cd rez-pipz
rez build --install
```

Here's how you use it.

```bash
rez env pipz -- install six
```

And here's how you install binary packages, specifically for the platform you are on.

```bash
rez env pipz -- install sqlalchemy
```

To install for a particular version of Python, include it in the initial request.

```bash
rez env python-2 pipz -- install sqlalchemy
```

- See [rez-pipz](https://github.com/mottosso/rez-pipz) for details.

<br>

### Install from Scoop

Scoop is a package manager for Windows. It's akin to [Chocolatey](), except packages are portable and doesn't require adminstrative access, which makes it a perfect fit for Rez.

```bash
git clone https://github.com/mottosso/rez-scoopz.git
cd rez-scoopz
rez build --install
```

Here's how you use it.

```bash
rez env scoopz -- install python
```

- See [rez-scoopz](https://github.com/mottosso/rez-scoopz) for details.

<br>

## Package version and Python

Every package containing a payload typically involves two version numbers.

- Version of the package
- Version of the payload

Preferably, these would always line up, but how can you expose the version of a package to Python?

**package.py**

```python
name = "my_library"
version = "1.0"
```

**my_library/python/my_library.py**

```python
version = "?"
```

### 1. Package to Python

What if Python was the one defining a version, and `package.py` picking this up instead? You certainly can, except it moves complexity away from your library and into your `package.py`, which is generally not a good idea.

**package.py**

Option 1, plain-text

```python
name = "my_library"

with open("python\my_library.py") as f:
    for line in f:
        if line.startswith("version = "):
            _, version = line.rstrip().split(" = ")
            break
```

This works, but makes a few fragile assumptions about how the version is formatted in the file.

Option 2.

```python
import os
name = "my_library"

cwd = os.getcwd()
os.chmod("python")
import my_library
version = my_library.version
```

This is a little ugly, but works. The assumption made is that whatever is being executed in the imported module doesn't have any side effects or negatively impacts performance. Some modules, for example, establish database connections or temporary directories on import.

<br>

### 2. Embedded

This next approach addresses the above concerns in a more compact manner.

In order to use a package, it must first be built. We can leverage this build step to modify a Python library and embed the package version.

**my_library/__init__.py**

```py
try:
    from . import __version__
    version = __version__.version
except ImportError:
    version = "dev"
```

At this point, `version` will read `"dev"` until the module `__version__.py` has been written into the library. We can write this file during build.

**package.py**

```python
name = "my_library"
version = "1.0"
build_command = "python {root}/install.py"
```

**install.py**

```python
import os
import shutil

root = os.path.dirname(__file__)
build_dir = os.environ["REZ_BUILD_PATH"]

# Copy library
shutil.copytree(os.path.join(root, "my_library"),
                os.path.join(build_dir, "my_library"))

# Inject version
version_fname = os.path.join(build_dir, "my_library", "__version__.py")
version = os.getenv("REZ_BUILD_PROJECT_VERSION")

with open(version_fname, "w") as f:
    f.write("version = \"%s\"" % version)
```

And there you go. Now the version will read `"dev"` unless the package has been built, in which case it would read `"1.0"`.