### Prerequisities

This project requires Rez and memcached to be setup.

```bash
c:\python27\python pip install pip bleeding-rez -U --user
rez bind python
```

Next, setup your environmen. This can (and should) be stored in a `.bat` script of sorts.

```bash
set LOCAL_PACKAGES=%userprofile%\packages
set SERVER_PACKAGE_ROOT=\\studioanima.local\Main\common\tools\packages
set TD_PACKAGES=%SERVER_PACKAGE_ROOT%\td
set INTERNAL_PACKAGES=%SERVER_PACKAGE_ROOT%\int
set EXTERNAL_PACKAGES=%SERVER_PACKAGE_ROOT%\ext
set CONVERTED_PACKAGES=%SERVER_PACKAGE_ROOT%\converted
set REZ_PACKAGES_PATH=%LOCAL_PACKAGES%;%TD_PACKAGES%;%INTERNAL_PACKAGES%;%EXTERNAL_PACKAGES%;%CONVERTED_PACKAGES%
```

Finally, tell Rez about where to find memcached. Without this, resolving packages go from 0.1 seconds to 10+ seconds.

```bash
set REZ_MEMCACHED_URI=10.100.50.81:11211
```

<br>

### Usage

The project currently resides within a branch.

```bash
git clone https://gitlab.studioanima.co.jp/ishikawa_y/standalone-launchapp.git
cd standalone-launchapp
git checkout launchapp2
```

Finally, launch!

```bash
rez env PySide six -- python -m launchapp2 --root \\studioanima.local\Main\ANIMA\projects --verbose
```

Details:

- `rez env` establishes an environment with requirements
- Anything after `--` are commands run within that environment
- `PySide` and `six` are coming from the globally shared package repository, at `REZ_PACKAGES_PATH`.

<br>

### Code Convention

- **Data hierarchy** Data is hierarchically stored by human readable type, e.g. `widgets` and `panels`
- **Data persistence** Persistent data is stored in dictionaries, whereas transient data is stored in flat variables. E.g. `widgets = {"myWidget": QtWidgets.QWidget()}` versus `layout = QtWidgets.QHBoxLayout()`
- **Dictionary naming convention** Variables are written in snake_case, but keys of dictionaries are stored as camelCase.

<br>

### Debugging

Launch App accesses files and network using threads to avoid locking up the interface. Sometimes, threads can cause issues and so this flag can be used to disable use of threads alltogether. Under normal circumstances, you should find actions running quicker without threads, at the expense of user interactivity.

```bash
$ set LAUNCHAPP_NOTHREADING=True
```