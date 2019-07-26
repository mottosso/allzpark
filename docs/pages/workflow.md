This page is dedicated to best practices for working with Rez and Allzpark.

<br>

### Development Workflow

Whether you are writing a C++ or Python library, the general workflow goes something like this.

1. Edit source 
2. Call `rez build --install`
3. Reload library (e.g. Maya module or plug-in)
4. Test the library
5. Goto (1) until satisfied

Where `rez build --install` operates in two steps.

1. Create an internal `build\` directory with everything going into the installed package
2. Copy the `build\` directory into your `REZ_LOCAL_PACKAGES_PATH` as the specified version

This operation is destructive, in that it will overwrite what was already there. This is what allows you to keep rebuilding and testing your package, without having to increment the version for each line of source code changed.

<br>

### Release Workflow

One of the strenghts of Rez is that, whilst Git enables you to version control changes to code, Rez enables version control released software onto the floor. Once you're happy with an update or newly created package, it's time to release it.

```bash
cd my_package
rez build --install --release
```

This command will perform an identical operation to `rez build --install`, except packages written to `REZ_RELEASE_PACKAGES_PATH`.

Like `--install`, this operation is destructive, and most of the time you wouldn't want released packages to change. There are at least two methods for preventing that, both of which involve the use of **Git**.

1. Limit use of `--release` to a server-side application, like GitLab. For example, once your changes have been pushed and tagged, a CI pipeline could trigger a call to `--release` whereby the GitLab runner is the only one with write-access to the `REZ_RELEASE_PACKAGES_PATH`.
2. Use `rez release` which does something similar, except locally. It creates a tag identical to the proposed package version, pushed it to the currently set up Git remote.