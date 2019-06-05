![launchapp_1](https://user-images.githubusercontent.com/2152766/58943971-bee4c600-8778-11e9-8117-f50fe260cee0.gif)

### launchapp2

The Rez-based application launcher for film and games.

<br>

### Features

- Complete control over dependencies per-project
- Integration with Rez package management
- Per-package metadata, such as icons and label

<br>

### Prerequisities

```bash
pip install bleeding-rez PySide
```

Next, setup your environment. This can (and should) be stored in a `.bat` script of sorts.

```bash
:: Set these to something appropriate
set _LOCAL_PACKAGES=%userprofile%\packages
set _SERVER_PACKAGES=%userprofile%\.rez\packages

set REZ_PACKAGES_PATH=%_LOCAL_PACKAGES%;%_SERVER_PACKAGES%
```

<br>

### Usage

```bash
git clone https://github.com/mottosso/launchapp2.git
cd launchapp2
./launchapp2.bat
```

<br>

### Options

- Set `LAUNCHAPP_ROOT` to where your projects reside, defaults to `~/projects`
- Set `LAUNCHAPP_REQUIRE` to which requirements you'd like for launchapp2 to use.

**Requirements**

launchapp2 can be run with these versions.

- Python `2.7,3.6+`
- Qt `4,5`
- Qt-binding `PySide, PySide2, PyQt4 or PyQt5`

<br>

### Performance

Resolving packages can take some time, so to accelerate this process requests for packages can be cached within a server-side application called "memcached". Once you've got it running, resolving packages go from 0.1 seconds to 10+ seconds.


Prior to launching launchapp2, append this to your environment.

```bash
set REZ_MEMCACHED_URI=127.0.0.1:11211
```

> This would typically reside at a network address.

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

<br>

### More Gifs

![launchapp_2](https://user-images.githubusercontent.com/2152766/58943970-be4c2f80-8778-11e9-9344-66007ba5cb5b.gif)
![launchapp_3](https://user-images.githubusercontent.com/2152766/58943973-bee4c600-8778-11e9-809a-cf2aaf7c94c0.gif)
