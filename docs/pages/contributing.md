Thanks for considering making a contribution to the Allzpark project!

The goal of Allzpark is making film and games productions more fun to work on, for artists and developers alike. Almost every company with any experience working in this field has felt the pain of managing software and versions when all you really want to do is make great pictures. Allzpark can really help with that, and you can really help Allzpark!

<br>

### Architecture

The front-end is written in Python and [Qt.py](https://github.com/mottosso/Qt.py), and the back-end is [bleeding-rez](https://github.com/mottosso/bleeding-rez). You are welcome to contribute to either of these projects.

Graphically, the interface is written in standard Qt idioms, like MVC to separate between logic and visuals. The window itself is an instance of `QMainWindow`, whereby each "tab" is a regular `QDockWidget`, which is how you can move them around and dock them freely.

- [model.py](https://github.com/mottosso/allzpark/blob/master/allzpark/model.py)
- [view.py](https://github.com/mottosso/allzpark/blob/master/allzpark/view.py)
- [control.py](https://github.com/mottosso/allzpark/blob/master/allzpark/control.py)

User preferences is stored in a `QSettings` object, including window layout. See `view.py:Window.closeEvent()` for how that works.

<br>

### Guidelines

There are a few ways you can contribute to this project.

1. Use it and report any issues [here](https://github.com/mottosso/allzpark/issues)
1. Submit ideas for improvements or new features [here](https://github.com/mottosso/allzpark/issues)
1. Add or improve [this documentation](https://github.com/mottosso/allzpark/tree/master/docs)
1. Help write tests to avoid regressions and help future contributors spot mistakes

Any other thoughts on how you would like to contribute? [Let me know](https://github.com/mottosso/allzpark/issues).

<br>

### Documentation

The documentation you are reading right now is hosted in the Allzpark git repository on GitHub, and built with a static site-generator called [mkdocs](https://www.mkdocs.org/) along with a theme called [mkdocs-material](https://squidfunk.github.io/mkdocs-material/).

Mkdocs can host the entirety of the website on your local machine, and automatically update whenever you make changes to the Markdown documents. Here's how you can get started.

<div class="tabs">
  <button class="tab powershell " onclick="setTab(event, 'powershell')"><p>powershell</p><div class="tab-gap"></div></button>
  <button class="tab bash " onclick="setTab(event, 'bash')"><p>bash</p><div class="tab-gap"></div></button>
</div>

<div class="tab-content powershell" markdown="1">

You can either use Rez and Pipz.

```powershell
cd allzpark\docs
rez env pipz -- install -r requirements.txt
. serve.ps1
```

Or install dependencies into your system-wide Python.

```powershell
cd allzpark\docs
pip install -r requirements.txt
mkdocs serve
```

</div>

<div class="tab-content bash" markdown="1">

```bash
cd allzpark/docs
rez env pipz -- install -r requirements.txt
rez env git python mkdocs_material-4.4.0 mkdocs_git_revision_date_plugin==0.1.5 -- mkdocs serve
```

Or install dependencies into your system-wide Python.

```powershell
cd allzpark/docs
pip install -r requirements.txt
mkdocs serve
```

</div>

You should see a message about how to browse to the locally hosted documentation in your console.
