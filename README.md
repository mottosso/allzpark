<div align=center>
	<a href=https://allzpark.com><img src=https://user-images.githubusercontent.com/2152766/62561970-28b44580-b878-11e9-86df-2b2081a12809.png></a>
	<br>
	<p align=center><b>Application launcher</b> and <i>environment management</i><br>for 21st century games and digital post-production,<br>built with <a href=https://github.com/mottosso/bleeding-rez>bleeding-rez</a> and <a href=https://github.com/mottosso/Qt.py>Qt.py</a></p>
	<a href=https://mottosso.visualstudio.com/allzpark/_build/latest?definitionId=2&branchName=master><img src=https://mottosso.visualstudio.com/allzpark/_apis/build/status/mottosso.allzpark?branchName=master></a> <a href=https://pypi.org/project/allzpark/>
	<img src=https://badge.fury.io/py/allzpark.svg></a>
    <br>
    <img src=https://img.shields.io/badge/-PyQt4-green>
    <img src=https://img.shields.io/badge/-PyQt5-green>
    <img src=https://img.shields.io/badge/-PySide-green>
    <img src=https://img.shields.io/badge/-PySide2-green>
    <img alt=Windows title="Runs on Windows" height=16 src=https://user-images.githubusercontent.com/2152766/62287773-ba741b00-b452-11e9-8ad7-9a5152488de7.png>
    <img alt=Linux title="Runs on Linux" height=16 src=https://user-images.githubusercontent.com/2152766/62287771-b9db8480-b452-11e9-9bf1-45b40465ed54.png>
    <img alt=MacOS title="Runs on MacOS" height=16 src=https://user-images.githubusercontent.com/2152766/62287772-b9db8480-b452-11e9-9a88-4560388b97f4.png>
    <br>
    <img src=https://img.shields.io/pypi/pyversions/allzpark?color=steelblue>
    <a href="https://github.com/mottosso/bleeding-rez/"><img src=https://img.shields.io/pypi/v/bleeding-rez?color=steelblue&label=bleeding-rez></a>
</div>

<br>

#### News

| Date        | Release | Notes
|:------------|:--------|:----------
| August 2019 | 1.2 | First official release 

<br>

### What is it?

It's an application launcher, for when you need control over what software and which versions of software belong to a given project. It builds on the self-hosted package manager and environment management framework [bleeding-rez](https://github.com/mottosso/bleeding-rez), providing both a visual and textual interface for launching software in a reproducible way.

![](https://user-images.githubusercontent.com/2152766/61705822-7d1ad980-ad3e-11e9-81b3-473e8ac4e7c6.gif)

<br>

### Usage

Allzpark runs on Windows, Linux and MacOS, using Python 2 or 3 and any binding of Qt, and is available via `pip`.

```bash
pip install allzpark
```

See [Quickstart](https://allzpark.com/quickstart) for more details and tutorials.

**Some Table of Contents**

- [Landing Page](https://allzpark.com)
- [Getting Started](https://allzpark.com/getting-started)
- [Getting Advanced](https://allzpark.com/getting-advanced)
- [Getting Rez'd](https://allzpark.com/rez)
- [Contributing](https://allzpark.com/contributing)
- [...](https://allzpark.com)

<br>

### Updating the Docs

I'd like for this to happen during CI, but till then there's a `deploy.ps1` in the `docs/` directory.

```bash
cd allzpark\docs
. deploy.ps1
```

This will build the docs and deploy it onto the `gh-pages` branch, which is reflected live after about 1 min.
