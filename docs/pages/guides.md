## In development

Allspark is currently [being developed](https://github.com/mottosso/allspark) and is not yet ready for use.

If you're interested in early-access to collaborate and or contribute, [get in touch](mailto:marcus@abstractfactory.io). A 1.0 is scheduled for release in early August 2019.

<br>
<br>
<br>

## Quickstart

By the time you're done with this chapter, you'll be able to call the below command, and understand when to use it.

```powershell
rez env allspark pyside2 python-3 -- allspark --root /my/projects
```

Where `/my/projects` is the absolute path to your project Rez packages.

<br>

### Setup

Allspark is all about Rez which is all about managing software, so first thing we need is get Rez setup.

```powershell
pip install bleeding-rez --user
rez bind --quickstart
git clone https://github.com/mottosso/rez-scoopz.git
git clone https://github.com/mottosso/rez-pipz.git
cd rez-scoopz
rez build --install
rez env scoopz -- install python git
cd ../rez-pipz
rez build --install
rez env pipz -- install pyside2 allspark
```

And there you have it.

```powershell
rez env pyside2 allspark -- allspark --root 
```

![image](https://user-images.githubusercontent.com/2152766/60429751-aa6ae080-9bf3-11e9-82bf-cc79ce99fe5c.png)

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
$ rez env pyside2 allspark bleeding_rez -- python -m allspark
==============================
 allspark (1.1.79)
==============================
- Loading Rez.. ok - 0.75s
- Loading Qt.. ok - 6.14s
- Loading allspark.. ok - 0.53s
- Loading preferences.. ok - 0.00s
------------------------------
```

Notice how long it took to load `Qt`, let's localise this.

```powershell
$ rez env localz -- localise PySide2
```

Now try launching again.

```powershell
$ rez env pyside2 allspark bleeding_rez -- python -m allspark
rez env pyside2 allspark bleeding_rez -- python -m allspark
==============================
 allspark (1.1.79)
==============================
- Loading Rez.. ok - 0.91s
- Loading Qt.. ok - 0.36s
- Loading allspark.. ok - 0.70s
- Loading preferences.. ok - 0.00s
------------------------------
```

That's much better.

**Disk Space**

To save disk space, you can delete any or all localised packages from your `~/.packages` path.

```powershell
start %USERPROFILE%\.packages
```