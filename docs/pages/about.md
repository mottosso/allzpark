This section outlines the rationale behind Allzpark, to help you determine whether or not it is of use to you.

<br>

### Background

Allzpark (a.k.a. LaunchApp2) started as a 4-month commission for the Japanese [Studio Anima](http://www.studioanima.co.jp/). Time was divided into roughly these parts.

1. **Week 0-0** Tour of physical building, infrastructure and crew
1. **Week 1-2** Requirements gathering, an evaluation if current system
1. **Week 3-4** Evaluation of off-the-shelf options, e.g. Rez
1. **Week 5-6** Evaluation of studio, system and personnel resources
4. **Week 7-8** Integration and testing of fundamental infrastucture software, Ansible
5. **Week 9-10** Research and development of Rez to fit the criteria and initial [prototype](https://github.com/mottosso/rez-for-projects)
1. **Week 11-12** Conversion of existing package repository
1. **Week 13-14** Implementation of graphical user interface, LaunchApp2
1. **Week 15-16** Refinement of features, including localisation
1. **Week 17-18** Final integration and training of staff

<br>

### Journal

Allzpark was initially an internal project, never intended to be open sourced. As a result, the first 2 months of development are locked away behind an internal journal for the company (due to disclosure of sensitive information).

Luckily, it was around this time that Allzpark got approved for open source and when I was able to start sharing its development publicly, so that you are able to take part in the design decisions made, the why and how. This way, you're able to accurately determine whether a solution to a new problem takes the original requirements into consideration; something all too often lost in software projects.

- [Journal](https://github.com/mottosso/allzpark/issues/1)

<br>

## Story time

When Hannah - working at a digital production company like Framestore or ILM - arrives at work in the morning, she typically types something like this into her console.

```powershell
go gravity
maya
```

What this does is put Hannah in the "context" of the `gravity` project. The subsequent call to `maya` then launches a given application, in this case Autodesk Maya. But which version? And why does it matter?

<br>

### A closer look

To better understand what's happening here, let's take a closer look at what these commands do. Following the command `go gravity`, a few things happen.

1. The argument `gravity` is correlated to a project (either on disk or database)
2. The project is associated with metadata, detailing what  software and versions are in use
	- `maya-2015`
	- `arnold-4.12`
    - `mgear-2.4`
	- `fbake-4.1`
	- `fasset-1.14`
	- `...`
3. The associated software is loaded into command-line `environment`

At this point, the subsequent command `maya` unambiguously refers to `maya-2015`, which is how Framestore - and virtually every visual effects, feature animation, commercial and games facility - is able to tie a specific version of each set of software to a given project.

Why is this important? The answer lies in **interoperability**.

You see, whatever comes out of Hannah's department must interoperate with subsequent departments. Like an assembly line, the pace of the line remains consistent till the end, and every tool depends on the output of whatever came before it.

This holds true for individual applications, like Maya or Visual Studio, but also sub-components of applications - plug-ins.

Take `arnold-4.12` as an example. This particular version needs to interoperate with `maya-2015`.

```powershell
		2015   2016   2017   2018   2019
maya      |--------------------------|
arnold-1  |-------|
arnold-2      |-----------|
arnold-3             |-----------|
arnold-4                  |----------|
```

In order to leverage `maya-2015` for a given project, your choice of `arnold` is limited to those that support it, or vice versa.

```powershell
                          interoperable
                             slice
maya      |-----------------|------|---|
arnold-1  |-------|         |      |
arnold-2      |-----------| |      |    
arnold-3             |------|------|
arnold-4                  |-|------|---|
                            |      |
```

This issue is compounded by the number of libraries and plug-ins you use for a given project. Consider `openimageio`, `qt`, `ilmbase` and other off-the-shelf projects you may want to employ in a given project, and you can start to get some idea of how narrow 

It is then further compounded by in-house development projects, such as  your [*pipeline*](http://getavalon.github.io).

None of this would have been a problem, if you were able to say:

1. We will ever only work on a single project at a time
1. We know which versions to use
1. We don't develop any new software ourselves

In which case you could simply install each of these applications and get to work. But more often than not, things change. And in order to facilitate this change, there needs to be a system in place to help manage the combinatorial complexity of applications, software, and projects.

<br>

### Rez Users

Here are some of the studios using Rez today, along with some approximate numbers (sources linked).

| Studio         | Active | People | Disk   | Packages | Versions | Frequency | Source
|:---------------|:-------|:-------|:-------|:---------|:---------|:----------|:-----------
| Anima          | 2019-  | 100    | 30 GB  | 199      | 2133     | 5 / day   | -
| RodeoFX        | 2019-  | 200    | 223 GB | 400      | 6732     | -         | [a][]
| Animal Logic   | 2018-  | 999    | 2 TB   | 1552     | 44939    | 20 / day  | [a][]
| Mackievision   | 2019-  | 500    |        |          |          |           | -
| Imageworks     | 2019-  | 999    |        |          |          |           | -
| Puppetworks    | 2019-  | 200    |        |          |          |           | -
| ToonBox        | 2017-  |        |        |          |          |           | [f][]
| Pixomondo      | 2019-  |        |        |          |          |           | [b][]
| Freefolk       | 2019-  |        |        |          |          |           | [b][]
| MPC            | 2019-  |        |        |          |          |           | [b][]
| Squeeze Studio | 2019-  |        |        |          |          |           | [c][]
| Mikros         | 2019-  |        |        |          |          |           | [c][]
| Brunch Studio  | 2019-  |        |        |          |          |           | [d][]
| WWFX           | 2019-  |        |        |          |          |           | [e][]

[a]: https://groups.google.com/forum/#!topic/rez-config/GMiof1NEQoo
[b]: https://groups.google.com/forum/#!searchin/rez-config/advice$20or$20tips$20on$20getting$20latest$20%7Csort:date/rez-config/-fmvH5mv9wM/cCWqh9BlFQAJ
[c]: https://groups.google.com/forum/#!searchin/rez-config/Proper$20way$20to$20resolve$20an$20environment$20for$20an$20embedded$20python$20environment%7Csort:date/rez-config/2IWclNTJEk0/4B_hGWuxBQAJ
[d]: https://groups.google.com/forum/#!msg/rez-config/Z7NdidsJNUY/2zYgVKsoEAAJ
[e]: https://groups.google.com/forum/#!topic/rez-config/j78X0Qv3arM
[f]: https://github.com/nerdvegas/rez/commit/8ca303d
