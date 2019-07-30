This page will get you up and running with Allzpark in less than 2 minutes.

<br>

### Quickstart

The below commands will install Allzpark and its dependencies, including Rez.

```bash
python -m pip install allzpark --upgrade
rez bind --quickstart
allzpark --demo --clean
```

> Skip the `--clean` flag to preserve preferences, such as window layout, between runs.

<br>

#### Troubleshooting

Everything ok?

??? quote "pip not found"
    It's possible you have `pip` installed, just not on your `PATH`. Try this.

    ```bash
    python -m pip install bleeding-rez
    ```

    If this doesn't work, let's install pip.

    - [Reference](https://pip.pypa.io/en/stable/installing/)

    ```bash
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    ```

    If that didn't work, you may have to dive deeper into how to install pip for your platform.

    **Examples**

    - CentOS 7 - `yum install python-pip`
    - Ubuntu 18 - `apt install python3-pip`

    If that **did** work however, then if `pip` wasn't found, **Allzpark won't be either**. The `pip` executable is typically present on your PATH in the same location as Rez and Allzpark, and we need this to be the case.

    - On Windows, this path is typically `c:\python36\scripts` or `c:\python27\scripts`
    - On Linux, this path is `/usr/bin` and is much more likely already on your path
    - On MacOS, I'm not sure. [Let me know!](https://github.com/mottosso/allzpark/issues)

??? quote "Permission denied"
    The above command assumes admin/sudo access to your machine which isn't always the case. If so, you can install Rez using a virtual environment.

    **Python 3**

    ```bash
    $ python -m venv allzpark-venv
    $ allzpark-venv\Scripts\activate
    (allzpark-venv) $ pip install allzpark
    ```

    **Python 2**

    ```bash
    $ python -m pip install virtualenv
    $ python -m virtualenv allzpark-venv
    $ allzpark-venv\Scripts\activate
    (allzpark-venv) $ pip install allzpark
    ```

??? quote "rez not found"
    If installation went successfully, but you aren't able to call `rez` then odds are the Python executable path isn't on your `PATH`. On Windows, this directory is typically at `c:\python37\scripts` but may vary depending on how Python was installed, and varies across platforms.

    Following the installation of `rez`, you should have gotten a message about which path was missing from your `PATH`, you can either add this yourself, or use the `virtualenv` method from the above `Permission denied` box.

??? quote "Could not find ... PySide2"
    The instructions assume Python 3, but Allzpark is written with [Qt.py](https://github.com/mottosso/Qt.py) and supports any available binding, for both Python 2 and 3.

    Try installing Allzpark dependencies manually, replacing PySide2 with PySide(1).

    ```bash
    pip install --no-deps PySide allzpark allzparkdemo bleeding-rez
    ```

    If that doesn't work, then you can also use an [installer for PyQt4](https://stackoverflow.com/questions/22640640/how-to-install-pyqt4-on-windows-using-pip) or check the package management system of your platform.

??? quote "Something else happened"
    Oh no! I'd like to know about what happened, please let me know [here](https://github.com/mottosso/allzpark/issues) or send me a private message at [marcus@abstractfactory.io](mailto:marcus@abstractfactory.io).

<br>

#### Result

If everything went well, you should now be presented with this!

![image](https://user-images.githubusercontent.com/2152766/61855839-c68f3400-aeb8-11e9-9df5-d31a39b6e028.png)

<br>

### Next Steps

From here, try launching your favourite application, navigate the interface and make yourself at home. Then have a look at these to learn more.

- [Create a new profile](/getting-started)
- [Create a new application](/getting-started/#your-first-application)
