### Allzpark

[![Build Status](https://mottosso.visualstudio.com/allzpark/_apis/build/status/mottosso.allzpark?branchName=master)](https://mottosso.visualstudio.com/allzpark/_build/latest?definitionId=2&branchName=master) [![](https://badge.fury.io/py/allzpark.svg)](https://pypi.org/project/allzpark/)

Application launcher and environment management tool for games and digital post-production, built on [Rez](https://github.com/mottosso/allzpark).

<br>

### Usage

> In early development. Stay tuned for a release.

Press the **Watch** icon top-right for notifications.

![image](https://user-images.githubusercontent.com/2152766/60902299-4dac9d00-a267-11e9-893d-b3801fa422e9.png)

![ALLZPARK_1](https://user-images.githubusercontent.com/2152766/58943971-bee4c600-8778-11e9-8117-f50fe260cee0.gif)

<br>

### Rez Integration

For production, Allzpark should be deployed as a Rez package, so as to facilitate running independent versions across multiple projects. Deploy Allzpark as a Rez package with [`rez-pipz`](https://github.com/mottosso/rez-pipz).

```bash
git clone https://github.com/mottosso/allzpark.git
cd allzpark
rez env pipz -- install . --prefix /path/to/packages
```

<br>

### Development

To make changes and/or contribute to Allzpark, here's how to run it from its Git repository.

```bash
git clone https://github.com/mottosso/allzpark.git
cd allzpark
python -m allzpark
```

From here, Python picks up the `allzpark` package from the current working directory, and everything is set to go. For use with Rez, try this.

```bash
# powershell
git clone https://github.com/mottosso/allzpark.git
cd allzpark
. env.ps1
> python -m allzpark
```

This will ensure a reproducible environment via Rez packages.

#### Versioning

You typically won't have to manually increment the version of this project.

Major and minor versions are incremented for breaking and new changes respectively, the patch version however is special. It is incremented automatically in correspondance with the current commit number. E.g. commit number 200 yields a patch number of 200. See `allzpark/version.py` for details.

To see the patch version as you develop, ensure `git` is available on PATH, as it is used to detect the commit number at launch. Once built and distributed to PyPI, this number is then embedded into the resulting package. See `setup.py` for details.

<br>

### More Gifs

> "launchapp2" was the internal working title during development at [Studio Anima](http://studioanima.co.jp)

![ALLZPARK_2](https://user-images.githubusercontent.com/2152766/58943970-be4c2f80-8778-11e9-9344-66007ba5cb5b.gif)
![ALLZPARK_3](https://user-images.githubusercontent.com/2152766/58943973-bee4c600-8778-11e9-809a-cf2aaf7c94c0.gif)
![ALLZPARK_4](https://user-images.githubusercontent.com/2152766/58946617-3cf79b80-877e-11e9-8887-df9a92cb1851.gif)
![ALLZPARK_8](https://user-images.githubusercontent.com/2152766/58959026-16485d80-879c-11e9-8964-e277490dbf5f.gif)
