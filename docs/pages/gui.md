This page is specifically about the Allzpark graphical user interface.

<br>

### Advanced Controls

In the [Preferences](#preferences) you'll find an option to enable "Advanced Controls". These are designed to separate what is useful to an artist versus a developer.

![image](https://user-images.githubusercontent.com/2152766/61855966-0bb36600-aeb9-11e9-8202-0bd9e6c98bed.png)

<br>

### Multiple Application Versions

Sometimes you need multiple versions of a single application accessible via the same profile. Per default, Allzpark only displays the latest version of the versions available.

**allzparkconfig.py**

Here's the default.

```py
def applications_from_package(variant):
    requirements = variant.requires or []

    apps = list(
        str(req)
        for req in requirements
        if req.weak
    )

    return apps
```

**allzparkconfig.py**

As you can see, the default only returns the one request for an application. But Allzpark will display every version you return, here's an example of that.

```py
def applications_from_package(variant):
    from allzpark import _rezapi as rez

    # May not be defined
    requirements = variant.requires or []

    apps = list(
        str(req)
        for req in requirements
        if req.weak
    )

    # Strip the "weak" property of the request, else iter_packages
    # isn't able to find the requested versions.
    apps = [rez.PackageRequest(req.strip("~")) for req in apps]

    # Expand versions into their full range
    # E.g. maya-2018|2019 == ["maya-2018", "maya-2019"]
    flattened = list()
    for request in apps:
        flattened += rez.find(
            request.name,
            range_=request.range,
        )

    # Return strings
    apps = list(
        "%s==%s" % (package.name, package.version)
        for package in flattened
    )

    return apps
```

<br>

### Applications from Data

In addition to the above, you could also specify applications explicitly in your profile data.

**Alita/package.py**

```py
name = "alita"
version = "1.0"
_data = {
    "apps": ["maya-2018", "vs-2019", "zbrush", "mudbox"]
}
```

**allzparkconfig.py**

```py
def applications_from_package(package):
    try:
        return package._data["apps"]

    except (AttributeError, KeyError):
        # If there isn't any data, just do what you normally do
        from allzpark.allzparkconfig import _applications_from_package

        # Every variable and function from allzparkconfig has this hidden
        # alternative reference, with a "_" prefix.
        return _applications_from_package(package)
```