![launchapp_1](https://user-images.githubusercontent.com/2152766/58943971-bee4c600-8778-11e9-8117-f50fe260cee0.gif)

### launchapp2

The Rez-based application launcher for film and games, built-on on [Rez](https://github.com/nerdvegas/rez) for both software and projects. See [Rez for Projects](https://github.com/mottosso/rez-for-projects) for an example.

> "launchapp2" is a working title, to change once having reached some level of maturity

<br>

### Features

- GUI and CLI parity, anything done visually may be done textually
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

Resolving packages can take some time, so to accelerate this process requests for packages can be cached within a server-side application called "memcached". Once you've got it running, resolving packages go from 10+ seconds to 0.1+ seconds.


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

### Package Types

To LA2, there exists 3 different kinds of packages.

- Software
- Application
- Project

Software encapsulate a library, either Python or otherwise, including all of its data, such as Python modules.

Projects reference both Applications and Software and may or may not include data, such as project specific shelves for Maya, an icon for LA2 or other kinds of metadata you would otherwise find in ftrack or Shotgun. They also include an environment specific to a given project, such as its name, location on disk. E.g. `spiderman-1.0`.

Applications include `maya` and `nuke` and unlike Software doesn't contain their payload. That is, the data is referenced from elsewhere, typically the local drive. This helps improve perf

<br>

### Beta versus Stable

LA2 distinguishes between packages suffixed with `.beta` and those that aren't.

- `texteditor-1.0.0`
- `texteditor-1.1.0.beta`

Per default, these beta-versions are invisible and must be explicitly required. The idea is to facilitate the development of new versions, without affecting a stable environment. Beta versions are opt-in, meaning a user is able to gamble with an environment so long as it's intended.

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
![launchapp_4](https://user-images.githubusercontent.com/2152766/58946617-3cf79b80-877e-11e9-8887-df9a92cb1851.gif)
![launchapp_5](https://user-images.githubusercontent.com/2152766/58949561-a5e21200-8784-11e9-8796-d99736c84835.gif)
![launchapp_6](https://user-images.githubusercontent.com/2152766/58950543-f5c1d880-8786-11e9-88f2-08204f5ac1d9.gif)
![launchapp2_7](https://user-images.githubusercontent.com/2152766/58956502-5ad0fa80-8796-11e9-9596-01ca80d32317.gif)
![launchapp_8](https://user-images.githubusercontent.com/2152766/58959026-16485d80-879c-11e9-8964-e277490dbf5f.gif)
