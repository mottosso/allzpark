The starting point to using and understanding Allzpark.

<br>
<br>
<br>

## Goal

> Estimated reading time: 20 mins

By the time you're done with this chapter, you'll be able to call the below command, and understand what it does.

```powershell
rez env allzpark bleeding_rez-2.31+ pyside2 python-3 -- allzpark
```

<br>

## Package Management

Allzpark isn't just a pretty face, it's the backbone of any competent production studio working in visual effects, feature animation, commercials or games.

That backbone is made up of **packages**.

### What is a package?

A package is a group of files with some metadata attached, declaring a name, version and its relationship to other packages. When one package requires another, a *requirement hierarchy* is formed.

For example, consider this requirement.

```
requires = ["maya-2019", "arnold", "cmuscle"]
```

From looking at this, you'd expect a version of `arnold` and `cmuscle` compatible with `maya-2019` (note that we didn't request a particular version of these). Because only a subset of versions of `arnold` are compatible with `maya-2019` what happens is a *resolve*.

### Resolve

Resolving a request means solving the equation of a *requirements hierarchy* until exact versions of each package in a request is found, and goes something like this.

```powershell
iteration 01 # maya-2019 arnold cmuscle
iteration 02 # maya-2019.0.3 arnold-4.12 cmuscle-1.4
iteration 03 # maya-2019.0.3 arnold-4.12 cmuscle-1.4 libpng-12 libtiff-1 qt-5.12
iteration 04 # maya-2019.0.3 arnold-4.9 cmuscle-1.4 libpng-12 libtiff-1 qt-5.12 qtbase-5.12 qtgui-5-12 openiio-3.41
complete
```

1. In this example, the first iteration is your original request.
2. The second iteration expands on this request to include specific versions of `arnold` and `cmuscle`; both of which are deemed compatible with `maya-2019`.
3. Now things start to get interesting, where did `libpng-12` come from?! Well, that's a requirement of `arnold-4.12`, so if we want `arnold` we're going to have to get its other requirements too.
4. But see, now things get even more interesting. `arnold-4.12` was just downgraded to `arnold-4.9`! That's because `openiio` was a requirement of `qt` and conflicts with `arnold-4.12`. As a result, an older version of `arnold` was picked, one that is compatible with `openiio-3.41`.

!!! hint "Fun fact"
    That last step is one of the thing that separates Rez from package managers like `pip` and `conda`; the retroactive downgrading of a version to conform to a given constraint. This is one of the things that makes Rez **more capable** and **safer** than your typical resolver.

As you can see, the number of iterations and complexity therein can grow significantly. It is not uncommon for the number of packages involved to grow into the hundreds and run for dozens to hundreds of iterations per solve, with both off-the-shelf software like above and internally developed projects intermingled. Think about what you would have to go through to solve such a hierarchy yourself - which many do.

<br>

## Prerequisities

To resolve requirements, we'll utilise [bleeding-rez](https://github.com/mottosso/bleeding-rez).

```bash
pip install bleeding-rez
rez bind --quickstart
rez --version
# bleeding-rez 2.33.1
```

**Troubleshooting**

??? quote "`pip` not found"
    It's possible you have `pip` installed, just not on your `PATH`. Try this.

    ```powershell
    python -m pip install bleeding-rez
    ```

    If this doesn't work, let's install pip.

    - [Reference](https://pip.pypa.io/en/stable/installing/)

    ```bash
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    ```

??? quote "`Permission denied`"
    The above command assumes admin/sudo access to your machine which isn't always the case. If so, you can install Rez using a virtual environment.

    ```bash
    $ python -m pip install virtualenv
    $ python -m virtualenv rez-install
    $ rez-install\Scripts\activate
    (rez-install) $ pip install bleeding-rez
    ```

??? quote "`rez` not found"
    If installation went successfully, but you aren't able to call `rez` then odds are the Python executable path isn't on your `PATH`. On Windows, this directory is typically at `c:\python37\scripts` but may vary depending on how Python was installed, and varies across platforms.

    Following the installation of `rez`, you should have gotten a message about which path was missing from your `PATH`, you can either add this yourself, or use the `virtualenv` method from the above `Permission denied` box.

This will make `rez` available via the command-line and establish a few default "packages" in your `~/packages` directory, which we'll talk about later.

<br>

## Your first project

In order launch an application in the context of a project using Allzpark, we must create one.

![image](https://user-images.githubusercontent.com/2152766/60737328-46794c80-9f52-11e9-9601-7cf7d58f96ee.png)

### Spiderman

Your project will be a directory with a file inside called `package.py`.

```powershell
mkdir spiderman
cd spiderman
touch package.py
```

This will create a new file called `package.py` in your newly created `spiderman` directory. Edit this file with the following.

**package.py**

```python
name = "spiderman"
version = "1.0"
build_command = False
```

Now we can "build" and make use of it.

```powershell
rez build --install
$ rez env spiderman
> $ 
```

> The `>` character denotes that you are in a Rez "context", which is its virtual environment.

### Environment

Let's keep going

**package.py**

```python
name = "spiderman"
version = "1.1"
build_command = False

def commands():
    global env
    env["PROJECT_NAME"] = "Spiderman"
```

Now what happens?

```powershell
> $ exit
$ rez build --install
$ rez env spiderman
> $ Write-Host $env:PROJECT_NAME
Spiderman
```

### Requirements

Great, we're now in control over the environment of this package. What about requirements?

**package.py**

```python
name = "spiderman"
version = "1.2"
build_command = False
requires = ["texteditor"]

def commands():
    global env
    env["PROJECT_NAME"] = "Spiderman"
```

Now `spiderman` requires `texteditor` in order to run. Let's build it.

```bash
> $ exit
$ rez build --install
09:15:46 ERROR    PackageFamilyNotFoundError: package family not found: texteditor
```

### Your first application

Woops! We haven't got a package for `texteditor`, let's make one.

```powershell
> $ exit
$ cd ..
$ mkdir texteditor
$ cd texteditor
$ touch package.py
```

**texteditor/package.py**

```python
name = "texteditor"
version = "1.0"
build_command = False

def commands():
    import os
    global alias

    if os.name == "nt":
        alias("texteditor", "notepad")
    else:
        alias("texteditor", "nano")
```

Now let's build and use this package.

```powershell
$ rez build --install
$ rez env spiderman
> $ texteditor
```

Viola, a platform-dependent text editor, tied to a given project. This is one way of tying applications to a project, but we'll look at some more as we go along. In general, you'll want to keep packages self-contained and portable, such that you can deploy them elsewhere. In this case, we utilised a widely accessible application we can expect to exist on almost any workstation. But we aren't always so lucky.

### Another application

Let's make another one to illustrate this point.

```powershell
> $ exit
$ cd ..
$ mkdir maya
$ cd maya
$ touch package.py
```

**maya/package.py**

```python
name = "maya"
version = "2018.0"
build_command = False

def commands():
    import os
    global alias

    if os.name == "nt":
        alias("maya", r"c:\program files\autodesk\maya2018\bin\maya.exe")
    else:
        alias("maya", "/usr/autodesk/maya2018/bin/maya.bin")
```

In this example, we're making some assumptions that may or may not be appropriate for your environment. If you are in control over workstations and installation paths, then this is fine. But if you can't make that guarantee, you'll care about *portability* which we'll cover a little later.

!!! example "Exercise"
    Before we move on, make another package for `maya-2019` as well in a similar fashion. We'll need this for later.

<br>

## Weak References

Let's now update our project to require `maya` and see what we end up with.

![image](https://user-images.githubusercontent.com/2152766/60737361-6a3c9280-9f52-11e9-8139-7ccc67b2c60c.png)

**spiderman/package.py**

```python
name = "spiderman"
version = "1.3"
build_command = False
requires = ["texteditor-1", "maya-2018"]

def commands():
    global env
    env["PROJECT_NAME"] = "Spiderman"
```

To run it..

```powershell
$ rez env spiderman
> $ maya
> $ texteditor
```

As you can see, you now have both `maya` and `texteditor` available, at the same time. This typically is not what you want, and comes with a few gotchas. Consider for example if `texteditor` had a requirement for another project, such as `msvcrt<=2011`, and that `maya` has a similar but conflicting requirement, such as `msvcrt>=2013`. In isolation, this isn't a problem, because you can happily run `texteditor` without requiring `maya` and vice versa. But because these are both requirements of `spiderman`, you've now made `spiderman` impossible to use.

To account for this, we need to use "weak" references for both `texteditor` and `maya`.

**spiderman/package.py**

```python
name = "spiderman"
version = "1.4"
build_command = False
requires = ["~texteditor-1", "~maya-2018"]

def commands():
    global env
    env["PROJECT_NAME"] = "Spiderman"
```

Now when `spiderman` is requested, neither `maya` nor `texteditor` is included.

```powershell
~/spiderman $ rez build --install
~/spiderman $ rez env spiderman
> ~/spiderman $ maya
# Unrecognised command
```

Instead, you ask for them as part of your request.

```powershell
> spiderman/ $ exit
spiderman/ $ rez env spiderman maya
# resolved packages:
# maya-2018.0  ~\packages\maya\2018.0
```

But then, what was the point of making these requirements of `spiderman` if they weren't going to become part of the resolve unless? Surely you can just leave them out, and include `maya` in the request?

If you notice above, the resolved package was `maya-2018`. If it wasn't for this weak reference, Rez would have picked the latest version, `maya-2019`.

This is how you can tie applications to your project, without including each of them into the same context. Think about how chaotic this would be if your project involved dozens of applications!

<br>

## Allzpark

So you've made a project and given it a unique environment and applications. What's stopping you from launching these applications directly from the command-line? Why do you need Allzpark?

You don't!

Every command we've typed so far has been entirely in the hands of Rez and you can safely run productions in this way. What Allzpark does is put a face on this system, something for the less technical-minded artists to wrap their heads around, and establish a few ground-rules about how to make the most out of Rez. We'll get into these rules a little later, but for now, let's see what Allzpark looks like on your machine.

For this next part, we'll need `git`.

```powershell
git --version
# git version 2.16.1
```

??? quote "`git` not found"
    Git is required in later chapters, so you may as well get it up and running right away.

    - https://git-scm.com/

Allzpark is a Python package, and whilst we *could* install it like any other Python package, what we're going to do instead is install it as another Rez package. For that, we'll need `pipz`.

```powershell
git clone https://github.com/mottosso/rez-pipz.git
cd rez-pipz
rez build --install
```

`pipz` is a wrapper around `pip` for use with Rez. It can take any request `pip` can, and turn it into a Rez package. This saves from having to create a Rez package ourselves, when it's already a Python package. Neat!

To test out the installation, let's install `six` as Rez package.

```powershell
rez env pipz -- install six -y
```

This is the equivalent of `pip install six`. Now let's try it with Allzpark.

```powershell
git clone https://github.com/mottosso/allzpark.git
rez env pipz -- install ./allzpark
```

In this case, we'll install Allzpark from the cloned repository directly (as it isn't yet on PyPI). We'll also need a Qt binding. Any binding will do, in this example we'll use PySide2.

```powershell
rez env pipz -- install pyside2 -y
```

And there you have it. We are now ready to launch Allzpark.

```powershell
rez env allzpark python pyside2 -- allzpark --root ~/packages
```

![image](https://user-images.githubusercontent.com/2152766/60429751-aa6ae080-9bf3-11e9-82bf-cc79ce99fe5c.png)

<br>
<br>
<br>
<br>

<br>
<br>
<br>
<br>

<br>
<br>
<br>
<br>

<br>
<br>
<br>
<br>

## Under Development

<br>
<br>
<br>
<br>

<br>
<br>
<br>
<br>

<br>
<br>
<br>
<br>

<br>
<br>
<br>
<br>

## Shared Packages

One of the thing that separates Res from other package managers like `virtualenv` and `conda` is that packages you install are *shared*. Not only can they be shared across multiple machines, but also across multiple operating systems. Once a package has been installed, you'll never have to install it again. It is permanent, immutable in fact. This is how you can build up a personal- or studio-repository of packages that you can build a pipeline upon, making strong and controlled assumptions about what packages are available, which version they are at, and that they are compatible with each other.

So far, we've installed all packages into their default location, which is `~/packages`.

```bash
ls $env:USERPROFILE/packages  # With PowerShell
ls $HOME/packages  # With Bash
```

<br>

## Loading Order

If your graphical application depends on Qt.py, then Qt.py needs to be loaded *before* your application. This is where loading order comes in. By establishing a requirements hierarchy, the order in which libraries load is included for free.

<br>

## Package Path

The recommended layout for Rez packages are as follows.

![image](https://user-images.githubusercontent.com/2152766/60429696-8c04e500-9bf3-11e9-8b27-af355969d0bf.png)

- `int/` Internal projects, such as `core_pipeline`. You develop and release new versions internally.
- `ext/` External projects, such as `pyblish` and `Qt.py`, you typically install these with `rez env pipz -- install`
- `td/` Packages developed by TDs themselves, such as small utility scripts
- `proj/` Project such as `ATC` and `MST3`
- `app/` Applications, such as `maya` and `nuke`
- `converted/` Automatically converted packages from the old Template-based system

There are two additional paths.

- `~/packages` Your local development packages, from your home directory
- `~/.packages` Your [localised packages](#localisation)

<br>

## Pip

Any package from PyPI can be installed using a utility package called `pipz`.

```powershell
$ rez env pipz -- install pyblish-base --release
```

- See [rez-pipz](https://github.com/mottosso/rez-pipz) for details.

<br>

## Scoop

Any package from Scoop can be installed using another utility package called `scoopz`.

```powershell
$ rez env scoopz -- install python python27 git
```

- See [rez-scoopz](https://github.com/mottosso/rez-scoopz) for details.

<br>

## Localisation

For greater performance, any package may be localised to your local disk.

- See [rez-localz](https://github.com/mottosso/rez-localz) for details.

**Example**

```powershell
$ rez env pyside2 allzpark bleeding_rez -- python -m allzpark
==============================
 allzpark (1.1.79)
==============================
- Loading Rez.. ok - 0.75s
- Loading Qt.. ok - 6.14s
- Loading allzpark.. ok - 0.53s
- Loading preferences.. ok - 0.00s
------------------------------
```

Notice how long it took to load `Qt`, let's localise this.

```powershell
$ rez env localz -- localise PySide2
```

Now try launching again.

```powershell
$ rez env pyside2 allzpark bleeding_rez -- python -m allzpark
rez env pyside2 allzpark bleeding_rez -- python -m allzpark
==============================
 allzpark (1.1.79)
==============================
- Loading Rez.. ok - 0.91s
- Loading Qt.. ok - 0.36s
- Loading allzpark.. ok - 0.70s
- Loading preferences.. ok - 0.00s
------------------------------
```

That's much better.

**Disk Space**

To save disk space, you can delete any or all localised packages from your `~/.packages` path.

```powershell
start %USERPROFILE%\.packages
```

<br>

## Overrides

Packages, like Python modules, are discovered from a list of paths. If there are identical packages on two or more paths, the first one is picked.

We can leverage this behavior to *override* one package with another.

<br>

### Requirements

Overriding requirements enable you to test new packages, or packages of different versions, in an existing project and works like this.

1. Copy project onto local development directory
2. Edit
3. Install

If the version remains the same *or higher* then your edited project is now picked up in place of the original, providing final control over which packages are used in a given project.

<br>

### Environment

Overriding environment variables can be achieved in a similar fashion to [requirements](#requirements), but is even more flexible.

Packages with regards to environment variables act akin to CSS, or Cascading Style Sheets, from the world wide web in that every change augments - or cascades - a previous change.

**a/package.py**

```python
def commands():
    global env
    env["PYTHONPATH"].append("/a")
```

**b/package.py**

```python
requires = ["a"]

def commands():
    global env
    env["PYTHONPATH"].append("/b")
```

In this example, the package `b` augments an existing `PYTHONPATH` created by package `a`. It does so by *appending* the value `"/b"`. You can also `prepend` and overwrite by assigning it directly.

- `env[].append("")`
- `env[].prepend("")`
- `env[] = ""`

<br>

#### Example - Legacy Viewport

We can leverage this behavior to override the behavior of a program using dedicated "override packages".

**maya_legacy_viewport/package.py**

```python
name = "maya_legacy_viewport"
version = "1.0"
requires = ["maya"]

def commands():
    global env
    env["MAYA_ENABLE_LEGACY_VIEWPORT"] = "1"
```

Including this package in your resolve results in Maya exposing the Legacy Viewport option, to circumvent that pesky Viewport 2.0.

<br>

### Performance

Rez is heavily dependent on a server-side application called `memcached`, which as the name suggests is a cache for queries involving the filesystem. Without it, resolving new environments can take seconds to minutes compared to milliseconds, so it's recommended that you set it up.

??? quote "With Docker"
    If you've got access to Docker, then this is the simplest option for both a local and distributed install.

    ```bash
    docker run -ti --rm -p 11211:11211 memcached
    ```

    This will expose `memcached` to its default port 11211.

??? quote "With RaspberryPi"
    Memcached isn't particularly memory intensive (>=32 mb of RAM) and can run on low-end hardware like a Pi, and should keep you covered up to 500 versions or so.

    ```bash
    apt-get install memcached
    ```

    This will expose `memcached` to its default port 11211.

??? quote "Bare metal"
    You can also install onto your local machine, however it requires a Linux or MacOS operating system for that.

    - https://www.memcached.org/downloads
