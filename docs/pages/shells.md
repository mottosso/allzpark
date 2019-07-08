Rez provides support for a number of shells on Windows, Linux and MacOS. Each of which operate almost identically, some having their own special powers.

**Supported shells**

- [Windows PowerShell](#powershell)
- [cmd](#cmd)
- [bash](#bash)

<br>

## PowerShell

On Windows, you'll likely want to use PowerShell.

> Note that "Windows Powershell" is different from PowerShell 6 and above which is cross-platform but not yet supported by Rez.

- Aliases are created as `function ()`

**Resources**

- [Scoop Package Manager](https://www.youtube.com/watch?v=a85QLUJ0Wbs)
- [Why PowerShell](https://github.com/lukesampson/scoop/wiki/Why-PowerShell)
- [Getting Started](https://www.youtube.com/watch?v=IHrGresKu2w)
- [PowerShell Masterclass](https://www.youtube.com/playlist?list=PLlVtbbG169nFq_hR7FcMYg32xsSAObuq8)

### Process Management

PowerShell, like Python, works with objects rather than text like `cmd` and `bash`.

```powershell
PS> $fx = get-process -name firefox
PS> $fx.path
# C:\Program Files\Mozilla Firefox\firefox.exe
PS> $fx.workingset / 1mb
# 414.23828125
PS> $fx.kill()
```

### Aliases

```powershell
PS> ls
# 
#     Directory: C:\Users\marcus\.ssh
# 
# Mode                LastWriteTime         Length Name
# ----                -------------         ------ ----
# -a----       11/02/2018     15:52           1766 id_rsa
# -a----       18/02/2018     11:30           1486 id_rsa.ppk
# -a----       11/02/2018     15:52            392 id_rsa.pub
# -a----       18/03/2019     08:05           3514 known_hosts

PS> get-alias clear
# CommandType     Name                                               Version    Source
# -----------     ----                                               -------    ------
# Alias           cls -> Clear-Host
```

### Working with processes

`Get-Member` is akin to Python's `dir()`.

```powershell
PS> $notepad = start-process notepad -passthru
PS> $notepad | get-member
#    TypeName: System.Diagnostics.Process
# 
# Name                       MemberType     Definition
# ----                       ----------     ----------
# ...
# Name                       AliasProperty  Name = ProcessName
# Company                    ScriptProperty System.Object Company # {get=$this.Mainmodule.FileVersionInfo.CompanyName;}
# ...
# Path                       ScriptProperty System.Object Path {get=$this.Mainmodule.FileName;}
# WorkingSet                 Property       int WorkingSet {get;}
# Kill                       Method         void Kill()
# Refresh                    Method         void Refresh()
# Start                      Method         bool Start()
# ToString                   Method         string ToString()
# ...
PS> $notepad.company
# Microsoft Corporation
```

### .bashrc on PowerShell

Also found out that PowerShell has a startup script like Bash does; that's amazing. It means you can store not just environment variables "globally" but also functions and aliases like with Bash.

```powershell
PS> $profile
# C:\Users\marcus\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
PS> echo 'set-alias -name eco -value echo' >> $profile
```

### Run with double-click

Normally, `.ps1` scripts, unlike `.bat`, open with notepad. Here's how you can change that.

> This time you do need to be admin, unless there's another variable for the local user?

```powershell
PS> reg add "HKEY_CLASSES_ROOT\Microsoft.PowerShellScript.1\Shell\Open\Command" /d "\`"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe\`" -noLogo -ExecutionPolicy unrestricted -file \`"%1\`""
# Value  exists, overwrite(Yes/No)? yes
# The operation completed successfully.
```

The interesting bit being `ExecutionPolicy unrestricted`. Running PS scripts are not allowed per default on Windows. You can either allow it per invokation like this, or globally like this:

```powershell
Set-ExecutionPolicy unrestricted -scope CurrentUser
```

### Commands to variables

Like Bash, the result of a command can be passed to a variable.

```powershell
PS> $cd = "$(pwd)"
```

This example is particularly important, as `$(pwd)` in Bash returns a string (Bash doesn't have types) whereas in PS it returns an object. Wrapping it in `"` is akin to `str()` in that it converts the object to its string representation.

```powershell
$ mkdir temp
$ cd "$(pwd)\temp"
```

The cool thing about an object is that it's got properties and methods. :)

```powershell
PS> $(pwd) | Get-Member
# 
#    TypeName: System.Management.Automation.PathInfo
# 
# Name         MemberType Definition
# ----         ---------- ----------
# Equals       Method     bool Equals(System.Object obj)
# GetHashCode  Method     int GetHashCode()
# GetType      Method     type GetType()
# ToString     Method     string ToString()
# Drive        Property   System.Management.Automation.PSDriveInfo Drive {get;}
# Path         Property   string Path {get;}
# Provider     Property   System.Management.Automation.ProviderInfo Provider {get;}
# ProviderPath Property   string ProviderPath {get;}
```

### Undo/Redo

Yes, ctrl+z/ctrl+y works on the command-line, similar to a text-editor.

### Ctrl+Space

You can list commands from a partial entry with ctrl+space.

![powershell_ctrlspace](https://user-images.githubusercontent.com/2152766/59553473-5c1bd780-8f8d-11e9-8e90-eee6faf1fc32.gif)

### Send to Clipboard

```powershell
PS> get-process | clip
```

And ctrl+v to paste.

### Navigate registry and environment like files

Apparently, PS doesn't distinguish between what is a filesystem and what is an environment or registry, each referred to as a "drive".

```powershell
PS> cd c:
PS> cd hkcu:
PS> cd env:
PS> pwd
Path
----
Env:\

PS> Get-PSDrive                                                                     
Name           Used (GB)     Free (GB) Provider      Root
----           ---------     --------- --------      ----
Alias                                  Alias
C                 460.97         13.79 FileSystem    C:\
Cert                                   Certificate   \
Env                                    Environment
Function                               Function
HKCU                                   Registry      HKEY_CURRENT_USER
HKLM                                   Registry      HKEY_LOCAL_MACHINE
Variable                               Variable
WSMan                                  WSMan
```

### Get startup environment from running process

```powershell
PS> $maya = get-process -name maya
PS> $si = $maya.startupinfo
PS> $si.environment["PATH"]
C:\Program Files\Docker\Docker\Resources\bin;C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\Program Files\Git\cmd;C:\Program Files\Git\mingw64\bin;C:\Program Files\Git\usr\bin;C:\WINDOWS\System32\OpenSSH\
```

<br>

## cmd

Things to be aware of when using Rez with `cmd`.

### Long Environment Variables

`cmd.exe` is both familiar and available on every Windows machine dating back to Windows 95. It does however suffer from one major limitation; environment variables are limited in length to **2,000 characters**.

It isn't quite as simple as that, as there is a limit in the Windows API, another limit in `conhost.exe` and yet another in `cmd.exe`. When using Rez with `cmd.exe`, it is this limit you must take into consideration, and it is the most limiting of them all.

### History

A normal Rez context generates [a deep process hierarchy](../windows#process-tree).

1. Under normal circumstances, Rez is made available as `rez.exe`, generated by `pip install` into a virtual environment.
2. This executable calls another executable `python.exe` from that same install
3. Which in turn calls the parent Python process from which your virtual environment was made, e.g. `c:\python37\python.exe`
4. From here, Rez instantiates your `REZ_DEFAULT_SHELL`, e.g. `cmd`

That's 4 layers of processes, one calling the next.

It just so happens that 4 is the default number of buffers the windows ConHost.exe is configured to keep track of, which means that when you launch a 5th layer you lose history.

To account for this, configure your shell to keep track of 5 or more buffers.

![](https://user-images.githubusercontent.com/2152766/59965565-cc83a500-9507-11e9-859d-0df5b583b41c.png)

### Alias

The use of `alias()` in packages with `cmd.exe` has a few quicks worth considering.

- Utilises `doskey`, which works similar to `alias` on Linux
- Does not work with `rez env -- arbitrary command`
- Does not carry across shell, e.g. `start`
- Does not respect cmd.exe scope, e.g. `cmd /Q /K doskey python=c:\python27\python.exe $*` affects parent too

<br>

## bash

The default shell on Linux and MacOS.

- Aliases are created as `function()`