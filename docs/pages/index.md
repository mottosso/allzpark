template: landing.html

<div class="space"></div>

<div class="hboxlayout" id="landing">
    <div class="vboxlayout">
        <div class="container"><p id="title">Allzpark</p></div>
        <p>
            <img src=https://img.shields.io/badge/-Windows-blue>
            <img src=https://img.shields.io/badge/-Linux-blue>
            <img src=https://img.shields.io/badge/-MacOS-blue>
            <img src=https://img.shields.io/badge/-PyQt4-green>
            <img src=https://img.shields.io/badge/-PyQt5-green>
            <img src=https://img.shields.io/badge/-PySide-green>
            <img src=https://img.shields.io/badge/-PySide2-green>
            <br>
            <img src=https://img.shields.io/pypi/pyversions/allzpark?color=steelblue>
            <img src=https://img.shields.io/pypi/v/bleeding-rez?color=steelblue&label=bleeding-rez>
        </p>
        <div class="container">
            <p id="description">
                Powerful <b>application launcher</b> with <i>reproducible software environments</i>, for visual effects, feature animation and triple-A game productions.
            </p>
        </div>
        <br>
        <div class="hboxlayout justify-left">
            <a href="getting-started" class="button blue">Learn more</a>
            <a href="quickstart" class="button red">Download</a>
            <a href="https://github.com/mottosso/allzpark/issues/1" class="button green">Blog</a>
        </div>
        <br>
        <br>
    </div>
    <div class="container">
        <img class="poster" src=https://user-images.githubusercontent.com/2152766/60492033-02602080-9ca2-11e9-82f0-a3cc43cd5c5e.png>
    </div>
</div>

<div class="space"></div>
<div class="space"></div>
<div class="space"></div>
<div class="space"></div>

<!-- 

    Reproducible Environment

-->

<div class="hboxlayout row-reverse">
    <div class="vboxlayout" markdown="1">
        <h2>Package Based</h2>
        <p>
Works on your machine?
<br>
<br>
Allzpark is a package-based launcher, which means that everything related to a project is encapsulated into individual, version controlled and dependency managed "packages". Each coming together to form an environment identical across your development machine and anywhere your software is used.
<br>
</p>

```python
# A package definition
name = "blender"
version = "2.80"

def commands():
    global env
    env["PATH"].append("{root}/bin")
    env["PYTHONPATH"].prepend("{root}/python")
```

<p>
Establish complex relationships between software, applications and projects with <a href=https://github.com/mottosso/bleeding-rez>bleeding-rez</a>, the underlying framework powering Allzpark.
</p>
    </div>
    <div class="smallspace"></div>
    <img class="poster" style="border: none; box-shadow: none; padding: 0" src=https://user-images.githubusercontent.com/2152766/61705822-7d1ad980-ad3e-11e9-81b3-473e8ac4e7c6.gif>
</div>

<div class="space"></div>
<div class="space"></div>


<!-- 

    Command-line

-->

<div class="hboxlayout">
    <div class="vboxlayout">
        <h2>Dual Representation</h2>

<p>
Allzpark is but a shell.

Anything done via the GUI is available via the command-line, using standard Rez commands.
</p>

<div class="tabs">
  <button class="tab powershell " onclick="setTab(event, 'powershell')"><p>powershell</p><div class="tab-gap"></div></button>
  <button class="tab bash " onclick="setTab(event, 'bash')"><p>bash</p><div class="tab-gap"></div></button>
</div>

<div class="tab-content powershell" markdown="1">

```powershell
PS> rez env alita maya -q
> PS> echo "Hello Rez!"
> # Hello Rez!
```

</div>

<div class="tab-content bash" markdown="1">

```bash
$ rez env alita maya -q
> $ echo "Hello Rez!"
# Hello Rez!
```

</div>

</div>
<div class="smallspace"></div>
<img class="poster" src=https://user-images.githubusercontent.com/2152766/60496077-fbd5a700-9ca9-11e9-8ff4-09c272326fae.gif>
</div>

<div class="space"></div>
<div class="space"></div>

<!-- 

    Environment Management

-->

<div class="hboxlayout justify-left row-reverse">
    <div class="vboxlayout">
        <h2>Environment Management</h2>
<p>

Preview the environment, prior to launching an application. Make changes interactively as you develop or debug complex dependency chains.

</p>
    </div>
    <div class="smallspace"></div>
    <img class="poster" src=https://user-images.githubusercontent.com/2152766/60493787-82d45080-9ca5-11e9-9f0a-c5d7497b396f.gif>
</div>

<div class="space"></div>
<div class="space"></div>

<!-- 

    Customisation

-->

<div class="hboxlayout">
    <div class="vboxlayout">
        <h2>Customisation</h2>
        <p>
            Full theming support with pre-made color palettes to choose from. Interactively edit the underlying CSS and store them as your own.
            <br>
            <br>
            Drag panels around, establish a super-layout with everything visible at once.
        </p>
    </div>
    <div class="smallspace"></div>
    <img class="poster" style="border: none; box-shadow: none; padding: 0" src=https://user-images.githubusercontent.com/2152766/61289704-e1c7b880-a7c1-11e9-94ba-20ef7a2ca6bc.gif>
</div>


<br>
<br>
<br>
<br>
<br>
<br>

<div class="vboxlayout align-center">
    <div class="container"><p id="title">Allzpark</p></div>
    <p id="conclusion">
        Allzpark is free and <a href="https://github.com/mottosso/allzpark">open source</a> (LGPL)
        <br>
        Let's get this show on the road
    </p>
    <div class="hboxlayout justify-center">
        <a href="getting-started" class="button blue">Learn more</a>
        <a href="quickstart" class="button red">Download</a>
    </div>
</div>

<br>
<br>
<br>