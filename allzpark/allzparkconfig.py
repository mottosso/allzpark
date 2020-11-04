"""The Allzpark configuration file

Copy this onto your local drive and make modifications.
Anything not specified in your copy is inherited from here.

ALLZPARK_CONFIG_FILE=/path/to/allzparkconfig.py

"""

import os as __os


# Load this profile on startup.
# Defaults to the first available from `profiles`
startup_profile = ""  # (optional)

# Pre-select this application in the list of applications,
# if it exists in the startup profile.
startup_application = ""  # (optional)

# Default filter, editable via the Preferences page
exclude_filter = "*.beta"

# Where to go when clicking the logo
help_url = "https://allzpark.com"


def profiles():
    """Return list of profiles

    This function is called asynchronously, and is suitable
    for making complex filesystem or database queries.
    Can also be a variable of type tuple or list

    """

    try:
        return __os.listdir(__os.path.expanduser("~/profiles"))
    except IOError:
        return []


def applications():
    """Return list of applications

    Applications are typically provided by the profile,
    this function is called when "Show all apps" is enabled.

    """

    return []


def applications_from_package(variant):
    """Return applications relative `variant`

    Returns:
        list of strings: E.g. ['appA', 'appB==2019']

    """

    from . import _rezapi as rez

    # May not be defined
    requirements = variant.requires or []

    apps = list(
        str(req)
        for req in requirements
        if req.weak
    )

    return apps


def metadata_from_package(variant):
    """Return metadata relative `variant`

    Blocking call, during change of profile.

    IMPORTANT: this function must return at least the
        members part of the original function, else the program
        will not function. Very few safeguards are put in place
        in favour of performance.

    Arguments:
        variant (rez.packages_.Variant): Package from which to retrieve data

    Returns:
        dict: See function for values and types

    """

    data = getattr(variant, "_data", {})

    return dict(data, **{

        # Guaranteed keys, with default values
        "label": data.get("label", variant.name),
        "background": data.get("background"),
        "icon": data.get("icon", ""),
        "hidden": data.get("hidden", False),
    })


def themes():
    """Allzpark GUI theme list provider

    This will only be called once on startup.

    Each theme in list is a dict object, for example:

    {
        "name": "theme_name",
        "source": "my_style.css",
        "keywords": {"base-tone": "red", "res": "path-to-icons"},
    }

    * `name` is the theme name, this is required.
    * `source` can be a file path or plain css code, this is required.
    * `keywords` is optional, must be dict type if provided, will be
        used to string format the css code.

    Returns:
        list

    """
    return []


def application_parent_environment():
    """Application's launching environment

    You may want to set this so the application won't be inheriting current
    environment which is used to launch Allzpark. E.g. when Allzaprk is
    launched from a Rez resolved context.

    But if using bleeding-rez, and `config.inherit_parent_environment` is
    set to False, config will be respected and this will be ignored.

    Returns:
        dict

    """
    return None


def subprocess_encoding():
    """Codec that should be used to decode subprocess stdout/stderr

    See https://docs.python.org/3/library/codecs.html#standard-encodings

    Returns:
        str: name of codec

    """
    # nerdvegas/rez sets `encoding='utf-8'` when `universal_newlines=True` and
    # `encoding` is not in Popen kwarg.
    return "utf-8"


def unicode_decode_error_handler():
    """Error handler for handling UnicodeDecodeError in subprocess

    See https://docs.python.org/3/library/codecs.html#error-handlers

    Returns:
        str: name of registered error handler

    """
    import codecs
    import locale

    def decode_with_preferred_encoding(exception):
        encoding = locale.getpreferredencoding(do_setlocale=False)
        invalid_bytes = exception.object[exception.start:]

        text = invalid_bytes.decode(encoding,
                                    # second fallback
                                    errors="backslashreplace")

        return text, len(exception.object)

    handler_name = "decode_with_preferred_encoding"
    try:
        codecs.lookup_error(handler_name)
    except LookupError:
        codecs.register_error(handler_name, decode_with_preferred_encoding)

    return handler_name
