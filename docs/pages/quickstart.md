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

??? quote "No module named pip"
    For this to work, we'll need pip.

    - [Reference](https://pip.pypa.io/en/stable/installing/)

    ```bash
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    ```

    If that didn't work, have a look at to install pip for your platform.

    **Examples**

    - CentOS 7 - `yum install python-pip`
    - Ubuntu 18 - `apt install python3-pip`

??? quote "Permission denied"
    The above command assumes admin/sudo access to your machine which isn't always the case. If so, you can install Allzpark into a virtual environment.

    **Python 3**

    ```bash
    $ python -m venv allzpark-venv
    $ allzpark-venv\Scripts\activate
    (allzpark-venv) $ pip install allzpark --upgrade
    ```

    **Python 2**

    ```bash
    $ python -m pip install virtualenv
    $ python -m virtualenv allzpark-venv
    $ allzpark-venv\Scripts\activate
    (allzpark-venv) $ pip install allzpark --upgrade
    ```

??? quote "rez not found"
    If installation went successfully, but you aren't able to call `rez` then odds are the Python executable path isn't on your `PATH`. On Windows, this directory is typically at `c:\python37\scripts` but may vary depending on how Python was installed, and varies across platforms.

    Following the installation of `rez`, you should have gotten a message about which path was missing from your `PATH`, you can either add this yourself, or use the `virtualenv` method from the above `Permission denied` box.

    **Example message**

    ```powershell
    The script allzpark.exe and azp.exe are installed in 'C:\Python37\Scripts' which is not on PATH
    Consider adding this directory to PATH
    ```

??? quote "Something else happened"
    Oh no! I'd like to know about what happened, please let me know [here](https://github.com/mottosso/allzpark/issues).

<br>

#### Result

If everything went well, you should now be presented with this!

![image](https://user-images.githubusercontent.com/2152766/61855839-c68f3400-aeb8-11e9-9df5-d31a39b6e028.png)

<br>

### Next Steps

From here, try launching your favourite application, navigate the interface and make yourself at home. Then have a look at these to learn more.

> Note that the applications provided are examples and may not work as-is on your system.

- [Create a new profile](/getting-started)
- [Create a new application](/getting-started/#your-first-application)
