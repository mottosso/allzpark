This page carries on from a successful 👈 [quickstart](/quickstart) into making it relevant to your usecase.

<br>

### What is Allzpark?

It's an [application launcher](https://en.wikipedia.org/wiki/Comparison_of_desktop_application_launchers), similar to the one on the home screen of your phone or in the Start menu on Windows. The difference is that before actually launching the application, you are able to tailor the associated environment with data and requirements. An important aspect of any endevour involving multiple stakeholders, especially when requirements involve frequent change.

Here's how you would typically use Allzpark.

1. Boot machine
2. Boot Allzpark
3. Select [project](#what-is-a-project)
2. Boot [application](#what-is-an-application)

For the purposes of this quick walkthrough, I'll assume you are part of a visual effects studio whereby "project" means e.g. Alita and "application" means e.g. Blender.

<br>

#### What is a "project"?

Alita is the name given to a project within work is performed by multiple stakeholders towards a common goal, also referred to as a "show" or "game" depending on your context. It typically consists of these components.

- Name
- Version
- Applications
- Requirements
- Environment

Whereby "applications" are the software used to craft this project, such as Blender, Photoshop and Sublime Text.

The "requirements" indicate what software or libraries your project depend on, such as `python-3` or `git-2.21`.

The "environment" are hand-crafted variables stored in the launched application. Variables you can later refer back to in the software you write to run within the context of that application. For example, `PROJECT_NAME=alita` is a relevant variable to add, to allow for the application and your software to identify which project an application was launched in.

As you might have guessed, projects are *versioned* and we'll get into more about this and "packages" in general a little later.

<br>

#### What is an "application"?

Blender is an application within which work is performed.

In Allzpark, the project dictates which applications are available to the user, in order to faciliate a "data pipeline" being built around a pre-determined set of software and libraries.

An application typically consists of these components.

- Name
- Version
- Requirements
- Environment

Notice that it isn't unlike a project, and in fact not unlike any other software you'll encounter later on. These are both "packages" and we'll talk a lot more about what that is as we progress through this guide.

<br>

### Your first project

You and I are going to embark on a new project. Let's call it `kingkong`.

<br>

#### Command Line

The way we'll establish this project, and packages like it, is going to involve the command-line, so let's get comfortable with how it works.

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

Each project requires a folder and a file called `package.py`.

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
"@ | Out-File package.py
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

That's it, we've now got a brand new project. Let's add it to Allzpark and see what it looks like.

<div class="tabs">
  <button class="tab powershell " onclick="setTab(event, 'powershell')"><p>powershell</p><div class="tab-gap"></div></button>
  <button class="tab bash " onclick="setTab(event, 'bash')"><p>bash</p><div class="tab-gap"></div></button>
</div>

<div class="tab-content powershell" markdown="1">

```powershell
$env:MY_PROJECTS="kingkong"
allzpark --demo
```

</div>

<div class="tab-content bash" markdown="1">

```bash
export MY_PROJECTS="kingkong"
allzpark --demo
```

</div>

![image](https://user-images.githubusercontent.com/2152766/61939300-dd05c000-af8a-11e9-8a3d-429ce532e0d6.png)

We'll do a lot more of this as we go along, so don't worry if it doesn't quite make sense just yet.

!!! note "Regarding `MY_PROJECTS`"
    I've programmed this demo to take the environment variable `MY_PROJECTS` into account, but we'll have a look later at how you can customise how projects are actually discovered either from disk, a production tracking system like Shotgun or arbitrary function you provide.

<br>

#### What we've learned

Let's take a moment to reflect on what we've accomplished so far.

1. We've gotten familiar with the `rez` command
1. We've authored a new Rez package from scratch
1. We've used `rez build`, one of many Rez sub-commands, to build and install a package
1. We've made Allzpark aware of this new project package, via the `MY_PROJECTS` environment variable.

Next we'll have a look at how to add an application to your project, and how to actually make a new application from scratch.

<br>

### Your first application

There isn't much we can do with a project unless we've got an application, so let's add one.

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

As you may have guessed, these are the *requirements* of this project. That little squiggly `~` character ahead of `maya` indicates that this is a "weak" reference, which Allzpark interprets as application in this project.

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

Ok, but we didn't really create an application so much as just add an existing one to the project. Let's create a new application from your OS and add *that* to the project too.

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
"@ | Out-File package.py
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

You'll notice the similarity to creating a project and that's no coincidence. These are both Rez "packages". But there's something missing.

Unlike a project, an application must either reference an executable on disk, or encapsulate this executable into the package. We'll get into encapsulating files with a package a little later, for now let's have a look at how to reference a file on disk.

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
rez env texteditor
> texteditor
```

![image](https://user-images.githubusercontent.com/2152766/61943522-88b30e00-af93-11e9-9be3-b4e52923adf2.png)

This is the equivalent command-line procedure to what Allzpark is doing when you launch an application. Let's try it out in Allzpark too.

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

1. Creating a new application is not unlike creating a new project
1. Packages have a `commands()` function you can use to "bootstrap" an environment with custom commands
2. There's pros and cons to referencing system software, like a text editor.

<br>

### Your first payload

We've managed to make a new project, and an application and we're just about ready to start developing the next King Kong movie.

But there is something else missing. For the purposes of this chapter, I will assume you are developing King Kong using Autodesk Maya, but the same applies to just about any application.

!!! hint "In Development"
    Congratulations, you made it this far! I'm still working on this next bit, so stay tuned to this page for updates, or monitor the [GitHub repo](https://github.com/mottosso/allzpark) for changes as that's where these are coming from.
