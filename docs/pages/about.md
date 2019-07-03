This section outlines the rationale behind Allspark, to help you determine whether or not it is of use to you.

<br>

## Story time

When Hannah - working at ILM, Weta, MPC, Framestore, Goodbye Kansas or Double Negative - arrives at work in the morning, she typically types something like this into her console.

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