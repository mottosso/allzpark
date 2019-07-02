## In development

Allspark is currently [being developed](https://github.com/mottosso/allspark) and is not yet ready for use.

If you're interested in early-access to collaborate and or contribute, [get in touch](marcus@abstractfactory.io). A 1.0 is scheduled for release in early August 2019.

<br>
<br>
<br>

### Setup

The benefit of using Allspark is that it provides the power and flexibility of [Rez](https://github.com/mottosso/bleeding-rez) to developers and package authors and a graphical user interface for artists. Developers gain fine control over what software, libraries, applications and projects are made available to artists, along with any interdependencies therein.

For example, you may be working on Alita using a particular version of Maya, a specific set of plug-ins made available therein along with their versions, each of which needing to be compatible with both Maya and each other.

So the first thing we need to do is get you setup with Rez.

**Prerequisities**

- `git`
- `python-2.7+,<4.0`
- `pip-19+`

> Windows-only for now.

```bash
python -m pip install bleeding-rez --user
rez bind --quickstart
```

This will get Rez setup on your system.

<details><summary>Trouble?</summary>

If the above command didn't work, ensure your Python `bin/Scripts` path is available on `PATH`.

```bash
python -c "import rez;print(rez)"
# c:\Python37\Lib\site-packages\rez\__init__.py
```

```bash
# PowerShell
$env:PATH += ";c:\python37\scripts"

# cmd.exe
set PATH=c:\python37\Scripts;%PATH%
```

</details>

```bash
git clone https://github.com/mottosso/rez-scoopz.git
git clone https://github.com/mottosso/rez-pipz.git
cd rez-scoopz
rez build --install
```

Allspark is used to visually list applications in a given project, including their requirements.

```bash
python -m pip install bleeding-rez -U --user
rez env allspark bleeding_rez pyside2 -- python -m allspark
```

![image](https://user-images.githubusercontent.com/2152766/60429751-aa6ae080-9bf3-11e9-82bf-cc79ce99fe5c.png)

<br>

### Package Path

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

### External Packages - Pipz

Any package from PyPI can be installed using a utility package called `pipz`.

```bash
$ rez env pipz -- install pyblish-base --release
```

- See [rez-pipz](https://github.com/mottosso/rez-pipz) for details.

<br>

### External Packages - Scoopz

Any package from Scoop can be installed using another utility package called `scoopz`.

```bash
$ rez env scoopz -- install python python27 git
```

- See [rez-scoopz](https://github.com/mottosso/rez-scoopz) for details.

<br>

### Localisation

For greater performance, any package may be localised to your local disk.

- See [rez-localz](https://github.com/mottosso/rez-localz) for details.

**Example**

```bash
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

```bash
$ rez env localz -- localise PySide2
```

Now try launching again.

```bash
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

```bash
start %USERPROFILE%\.packages
```