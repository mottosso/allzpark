This page will get you up and running with Allzpark in less than 2 minutes.

<br>

### Quickstart

The below commands will install Allzpark and its dependencies, including Rez.

```bash
pip install allzpark -U
rez bind --quickstart
allzpark --demo
```

<br>

#### Troubleshooting

Did anything go wrong?

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

??? quote "Something else happened"
    Oh no! I'd like to know about what happened, please let me know [here](https://github.com/mottosso/allzpark/issues) or send me a private message at [marcus@abstractfactory.io](mailto:marcus@abstractfactory.io).

<br>

#### Result

If everything went well, you should now be presented with this!

![image](https://user-images.githubusercontent.com/2152766/61855839-c68f3400-aeb8-11e9-9df5-d31a39b6e028.png)

<br>

### Next Steps

From here, try launching your favourite application, navigate the interface and make yourself at home. Then have a look at these to learn more.

- [Create a new project](/getting-started)
- [Create a new application](/getting-started/#your-first-application)
