Short bite-sized snippets of information. This builds on information provided in the [guides](../guides) chapter.

<br>

## allzparkconfig.py

Configure allzpark using the `allzparkconfig.py`.

- `touch ~/allzparkconfig.py` Store in your `$HOME` directory
- `allzpark --config-file path/to/allzparkconfig.py` Or pass directly
- `ALLZPARK_CONFIG_FILE` Or pass via environment variable

All available keys and their default values can be found here.

- [allzparkconfig.py](https://github.com/mottosso/allzpark/blob/master/allzpark/allzparkconfig.py)

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
