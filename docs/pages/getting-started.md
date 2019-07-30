This page carries on from a successful 👈 [quickstart](/quickstart) into making it relevant to your usecase.

<br>

### What is Allzpark?

It's an [application launcher](https://en.wikipedia.org/wiki/Comparison_of_desktop_application_launchers), similar to the one on the home screen of your phone or in the Start menu on Windows. The difference is that before actually launching the application, you are able to tailor the associated environment within which the applicatuon runs.

??? info "For example..."
    Let's say you're working on a project using (1) Autodesk Maya, (2) Adobe Photoshop and (3) Pixologic Zbrush.

    ![image](https://user-images.githubusercontent.com/2152766/61997103-94d2c480-b094-11e9-81ba-6d8628649bcc.png)

    For Maya, you'd like to use various software libraries, Python scripts and binary plug-ins like Solid Angle's Arnold and Ziva Dynamics. However, each plug-in need to be of a particular version in order to play ball this version of Maya.

    ![image](https://user-images.githubusercontent.com/2152766/61997048-9059dc00-b093-11e9-8b03-ceac786f5785.png)

    Over time, the number of projects grow, as do the individual requirements of each application, and many of the plug-ins and libraries end up sharing dependencies with each other.

    ![image](https://user-images.githubusercontent.com/2152766/61997075-ff373500-b093-11e9-831b-bfa9e8c3c111.png)

    So now you've got a network of interdependencies that all need to work with each other and wonder..

    - "How can I write my own software that run in this environment?"
    - "How can I make sure my software runs once deployed?"

    That's where reproducible enironments come in handy and Allzpark can do for you.

    [Rez](https://github.com/mottosso/bleeding-rez) - an industry standard used by studios large and small - is the framwork with which you design this network and Allzpark is the shiny front-end your artists uses interface with it.

    **Studios using Rez**

    - [Studio Anima](https://studioanima.co.jp)
    - [Animal Logic](https://www.animallogic.com/)
    - [Sony Imageworks](https://www.imageworks.com/)
    - [Moving Picture Company](https://www.moving-picture.com/)
    - [Mikros Image](http://www.mikrosimage-animation.eu/en/)
    - And [many more](/about/#rez-users)

??? question "What are some similar projects?"
    Have a look at these, they solve a similar problem to Allzpark.

    - [Shotgun Launcher](https://support.shotgunsoftware.com/hc/en-us/articles/219032968-Application-Launcher)
    - [ftrack Connect](https://www.ftrack.com/en/2019/01/an-introduction-to-ftrack-connect.html)
    - [Mango Software Launcher](https://vimeo.com/126766739)

    So then, why should you choose Allzpark? Odds are you already have most of what these solutions offer and aren't ready for a complete swap. Allzpark integrates with existing pipelines and works standalone. It'll also work the day you decide to transition from e.g. Shotgun to ftrack, safeguarding your investment in each individual component of your pipeline.

Here's how you would typically use Allzpark.

1. Boot machine
2. Boot Allzpark
3. Select [profile](#what-is-a-profile)
2. Boot [application](#what-is-an-application)

For the purposes of this quick walkthrough, I'll assume you are part of a visual effects studio whereby "profile" means e.g. Alita and "application" means e.g. Blender.

<br>

<br>

#### What is a "profile"?

`alita` is the name given to a profile within which work is performed by multiple stakeholders towards a common goal. It typically consists of these components.

- Name
- Version
- Requirements
- Environment
- Applications

Whereby an "application" is the software used within this profile, such as `blender`, `photoshop` and `sublimetext`.

The "requirements" indicate what software or libraries your profile depend on, such as `python-3` or `git-2.21` or `arnold-6`.

The "environment" are hand-crafted variables stored in the launched application. Variables you can later refer back to in the software you write to run within the context of that application. For example, `PROJECT_NAME=alita` is a relevant variable to add, to allow for the application and your software to identify which profile an application was launched in.

As you might have guessed, projects are *versioned* and we'll get into more about this and "packages" in general a little later.

<br>

#### What is an "application"?

`blender` is an application within which work is performed.

In Allzpark, the profile dictates what applications are available to the user, in order to faciliate a "data pipeline" being built around a pre-determined set of software and libraries.

??? hint "Data pipeline?"
    A kind of "codified" workflow. For example, you use the same settings for whenever you export an image from Photoshop to your game engine. Rather than explicitly setting those each time, you make a script to turn the process into a single click. The same then applies to any kind of export and import of data in various applications, to and from various stakeholders in your company.

    These are some examples of pre-made "scripts" - in the form of frameworks - suitable for use with Allzpark.

    - [Avalon](http://getavalon.github.io)
    - [Kabaret](https://www.kabaretstudio.com/home)
    - [Piper](http://www.piperpipeline.com)
    - [Mango Pipeline](https://www.mangopipeline.com/)
    - [AnimationDNA](https://github.com/kiryha/AnimationDNA)
    - [Tik Manager](http://www.ardakutlu.com/tik-manager/)

An application typically consists of these components.

- Name
- Version
- Requirements
- Environment

Notice that it isn't unlike a profile, and in fact not unlike any other software you'll encounter later on. These are both "packages" and we'll talk a lot more about what that is as we progress through this guide.

<br>

#### What is an "package"?

I've talked a lot about "packages" and how great they are, but what exactly *are* they and why should you care?

<br>

### Your first profile

You and I are going to embark on a new profile. Let's call it `kingkong`

<br>

#### Command Line

The way we'll establish this profile, and packages like it, is going to involve the command-line, so let's get comfortable with how it works.

I'll provide command-line instructions for both `powershell` and `bash`, to cover both Windows, Linux and MacOS users. You can follow along using either of the two flavours, but odds are the one pre-selected is the one you'll want to use.

<div class="tabs">
  <button class="tab powershell " onclick="setTab(event, 'powershell')"><p>powershell</p><div class="tab-gap"></div></button>
  <button class="tab bash " onclick="setTab(event, 'bash')"><p>bash</p><div class="tab-gap"></div></button>
</div>

<div class="tab-content powershell" markdown="1">

```powershell
$env:POWERSHELL="These lines are for powershell"

$var = "If you are on Windows, this is where we'll
        spend most of our time. It also applies to
        pwsh, the cross-platform PowerShell 6+."
```

</div>

<div class="tab-content bash" markdown="1">

```bash
echo These lines are for bash
echo typically used in MacOS and Linux
```

</div>

Now select a shell of your choice and let's get going.

!!! hint "JavaScript"
    If you aren't seeing any code, make sure you have JavaScript enabled. If this is a problem for you, [let me know](https://github.com/mottosso/allzpark/issues).

<br>

#### King Kong

Each profile requires a folder and a file called `package.py`.

<div class="tabs">
  <button class="tab powershell " onclick="setTab(event, 'powershell')"><p>powershell</p><div class="tab-gap"></div></button>
  <button class="tab bash " onclick="setTab(event, 'bash')"><p>bash</p><div class="tab-gap"></div></button>
</div>

<div class="tab-content powershell" markdown="1">

```powershell
mkdir ~/kingkong
cd ~/kingkong
@"
name = "kingkong"
version = "1.0.0"
build_command = False
"@ | Add-Content package.py
rez build --install
```

</div>

<div class="tab-content bash" markdown="1">

```bash
mkdir ~/kingkong
cd ~/kingkong
echo name = "kingkong" >> package.py
echo version = "1.0.0" >> package.py
echo build_command = False >> package.py
rez build --install
```

</div>

That's it, we've now got a brand new profile. Let's add it to Allzpark and see what it looks like.

<div class="tabs">
  <button class="tab powershell " onclick="setTab(event, 'powershell')"><p>powershell</p><div class="tab-gap"></div></button>
  <button class="tab bash " onclick="setTab(event, 'bash')"><p>bash</p><div class="tab-gap"></div></button>
</div>

<div class="tab-content powershell" markdown="1">

```powershell
$env:MY_PROFILES="kingkong"
allzpark --demo
```

</div>

<div class="tab-content bash" markdown="1">

```bash
export MY_PROFILES="kingkong"
allzpark --demo
```

</div>

![image](https://user-images.githubusercontent.com/2152766/61939300-dd05c000-af8a-11e9-8a3d-429ce532e0d6.png)

We'll do a lot more of this as we go along, so don't worry if it doesn't quite make sense just yet.

!!! note "Regarding `MY_PROFILES`"
    I've programmed this demo to take the environment variable `MY_PROFILES` into account, but we'll have a look later at how you can customise how projects are actually discovered either from disk, a production tracking system like Shotgun or arbitrary function you provide.

<br>

#### What we've learned

Let's take a moment to reflect on what we've accomplished so far.

1. We've gotten familiar with the `rez` command
1. We've authored a new Rez package from scratch
1. We've used `rez build`, one of many Rez sub-commands, to build and install a package
1. We've made Allzpark aware of this new profile package, via the `MY_PROFILES` environment variable.

Next we'll have a look at how to add an application to your profile, and how to actually make a new application from scratch.

<br>

### Your first application

There isn't much we can do with a profile unless we've got an application, so let's add one.

1. Open `kingkong/package.py` in your favourite text editor
2. Edit it as follows.

```python hl_lines="2 5 6 7 8"
name = "kingkong"
version = "1.0.1"
build_command = False

requires = [
    "~maya==2018.0.6",
    "~blender==2.80.0",
]
```

As you may have guessed, these are the *requirements* of this profile. That little squiggly `~` character ahead of `maya` indicates that this is a "weak" reference, which Allzpark interprets as application in this profile.

!!! hint "Protip"
    If you're already familiar with Rez and think to yourself "This isn't very flexible", you're right. Looking for applications in the requirements section of a package is a default you can customise later via the `allzparkconfig.py:applications_from_package()` function.

We'll talk more about requirements next, let's install this package and launch Allzpark.

```bash
cd kingkong
rez build --install
allzpark --demo
```

![allzpark_kingkong](https://user-images.githubusercontent.com/2152766/61941483-7e8f1080-af8f-11e9-9192-235b5c139dfb.gif)

!!! hint "Protip"
    You'll notice the order in which you specified the applications are respected in the GUI.

<br>

#### An application package

Ok, but we didn't really create an application so much as just add an existing one to the profile. Let's create a new application from your OS and add *that* to the profile too.

You can pick any application you'd like, for the purposes of this guide I'll make a package for a text editor.

<div class="tabs">
  <button class="tab powershell " onclick="setTab(event, 'powershell')"><p>powershell</p><div class="tab-gap"></div></button>
  <button class="tab bash " onclick="setTab(event, 'bash')"><p>bash</p><div class="tab-gap"></div></button>
</div>

<div class="tab-content powershell" markdown="1">

```powershell
mkdir ~/texteditor
cd ~/texteditor
@"
name = "texteditor"
version = "1.5.0"
build_command = False
"@ | Add-Content package.py
rez build --install
```

</div>

<div class="tab-content bash" markdown="1">

```bash
mkdir ~/texteditor
cd ~/texteditor
echo name = "texteditor" >> package.py
echo version = "1.5.0" >> package.py
echo build_command = False >> package.py
rez build --install
```

</div>

You'll notice the similarity to creating a profile and that's no coincidence. These are both Rez "packages". But there's something missing.

Unlike a profile, an application must either reference an executable on disk, or encapsulate this executable into the package. We'll get into encapsulating files with a package a little later, for now let's have a look at how to reference a file on disk.

**texteditor/package.py**

```python hl_lines="5 6 7 8 9 10 11 12 13 14"
name = "texteditor"
version = "1.5.1"
build_command = False

def commands():
    import os
    global alias

    if os.name == "nt":
        alias("texteditor", r"notepad")
    elif os.name == "darwin":
        alias("texteditor", r"textedit")
    else:
        alias("texteditor", r"gedit")
```

The `commands()` function is called whenever your package is referenced, and `alias()` creates a command you can use from within a context. We're able to leverage regular Python imports and commands here as well, which is how we detect the running operating system.

!!! note "About assumptions"
    One of the issues with referencing system software like this is, well, how can we be sure these actually exist on the target operating system? For Windows it's a given, but what about Linux? We'll see this problem crop up again later, and is in fact already an issue with the pre-existing demo packages for Maya and Blender.

    For the purposes of this guide, these assumptions are fine and I'll show you later how you can avoid making them, and at what cost.

Let's try this out.

```bash
cd texteditor
rez build --install
rez env texteditor --paths $(allzparkdemo --packages)
> texteditor
```

![image](https://user-images.githubusercontent.com/2152766/61943522-88b30e00-af93-11e9-9be3-b4e52923adf2.png)

This is the equivalent command-line procedure to what Allzpark is doing when you launch an application. Don't worry too much about what `rez env` actually does right now, we'll talk a lot more about it later. Let's try this out in Allzpark too.

**kingkong/package.py**

```python hl_lines="2 9"
name = "kingkong"
version = "1.0.2"
build_command = False

requires = [
    "~maya==2018.0.6",
    "~blender==2.80.0",
    "~texteditor==1.5.1",
]
```

```bash
cd kingkong
rez build --install
allzpark --demo
```

![image](https://user-images.githubusercontent.com/2152766/61945604-4dffa480-af98-11e9-863d-3856d5654832.png)

And presto!

!!! hint "Protip"
    Notice that our terminal doesn't yet have an icon, and its name is all lowercase and plain. We'll address this next, in the [Payload](#your-first-payload) chapter.

<br>

#### What we've learned

You made it! Let's reflect on what we've learned so far.

1. Creating a new application is not unlike creating a new profile
1. Packages have a `commands()` function you can use to "bootstrap" an environment with custom commands
2. There's pros and cons to referencing system software, like a text editor.

<br>

### Your first payload

We've managed to make a new profile, and an application and we're just about ready to start developing the next King Kong movie.

But there is something else missing. For the purposes of this chapter, I will assume you are developing King Kong using Autodesk Maya, but the same applies to just about any application.

!!! hint "In Development"
    Congratulations, you made it this far! I'm still working on this next bit, so stay tuned to this page for updates, or monitor the [GitHub repo](https://github.com/mottosso/allzpark) for changes as that's where these are coming from.


<br>

### Your first environment

So your profile has got some custom data, that's perfect. Now let's add some *metadata* as well.

```python
name = "kingkong"
version = "1.0.2"
build_command = False

requires = [
    "~maya==2018.0.6",
    "~blender==2.80.0",
    "~texteditor==1.5.1",
]

def commands():
    global env
    env["PROJECT_ID"] = "12"
    env["PROJECT_NAME"] = "kingkong"
    env["PROJECT_FRAMERATE"] = "25"
    env["PROJECT_TAGS"] = "awesome,great,best"
```

!!! hint "In Development"
    Congratulations, you made it this far! I'm still working on this next bit, so stay tuned to this page for updates, or monitor the [GitHub repo](https://github.com/mottosso/allzpark) for changes as that's where these are coming from.
