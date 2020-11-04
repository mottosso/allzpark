import os
import re
import time
import traceback
import functools
import contextlib
import logging
import collections
import webbrowser
import subprocess

from .vendor import six
from .vendor.Qt import QtCore

_lru_cache = {}
_threads = []
_basestring = six.string_types[0]  # For Python 2/3
_log = logging.getLogger(__name__)
_timer = (time.process_time
          if six.PY3 else (time.time if os.name == "nt" else time.clock))

USE_THREADING = not bool(os.getenv("ALLZPARK_NOTHREADING"))


@contextlib.contextmanager
def timing():
    t0 = _timer()
    result = type("timing", (object,), {"duration": None})
    try:
        yield result
    finally:
        t1 = _timer()
        result.duration = t1 - t0


def delay(func, delay=50):
    """Postpone `func` by `delay` milliseconds

    This is used to allow Qt to finish rendering prior
    to occupying the main thread. Such as calling some
    CPU-heavy function on a `QPushButton.pressed` event,
    which would normally freeze the GUI without letting
    the button unclick itself, resulting in unexpected
    visual artifacts.

    """

    QtCore.QTimer.singleShot(delay, func)


def async_(func):
    """No-op decorator, used to visually distinguish async_ functions"""
    return func


def cached(func):
    """Cache returnvalue of `func`"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = "{func}:{args}:{kwargs}".format(
            func=func.__name__,
            args=", ".join(str(arg) for arg in args),
            kwargs=", ".join(
                "%s=%s" % (key, value)
                for key, value in kwargs.items()
            )
        )

        try:
            value = _lru_cache[key]
        except KeyError:
            value = func(*args, **kwargs)
            _lru_cache[key] = value

        return value
    return wrapper


def windows_taskbar_compat():
    """Enable icon and taskbar grouping for Windows 7+"""

    import ctypes
    ctypes.windll.shell32.\
        SetCurrentProcessExplicitAppUserModelID(
            u"allzpark")


if USE_THREADING:
    def defer(target,
              args=None,
              kwargs=None,
              on_success=lambda object: None,
              on_failure=lambda exception: None):
        """Perform operation in thread with callback

        Arguments:
            target (callable): Method or function to call
            callback (callable, optional): Method or function to call
                once `target` has finished.

        Returns:
            None

        """

        thread = Thread(target, args, kwargs, on_success, on_failure)
        thread.finished.connect(lambda: _threads.remove(thread))
        thread.start()

        # Cache until finished
        # If we didn't do this, Python steps in to garbage
        # collect the thread before having had time to finish,
        # resulting in an exception.
        _threads.append(thread)

        return thread

else:
    # Debug mode, execute "threads" immediately on the main thread
    _log.warning("Threading disabled")

    def defer(target,
              args=None,
              kwargs=None,
              on_success=lambda object: None,
              on_failure=lambda exception: None):
        try:
            result = target(*(args or []), **(kwargs or {}))
        except Exception as e:
            on_failure(e)
        else:
            on_success(result)


class Thread(QtCore.QThread):
    succeeded = QtCore.Signal(object)
    failed = QtCore.Signal(Exception, _basestring)

    def __init__(self,
                 target,
                 args=None,
                 kwargs=None,
                 on_success=None,
                 on_failure=None):
        super(Thread, self).__init__()

        self.args = args or list()
        self.kwargs = kwargs or dict()
        self.target = target
        self.on_success = on_success
        self.on_failure = on_failure

        connection = QtCore.Qt.BlockingQueuedConnection

        if on_success is not None:
            self.succeeded.connect(self.on_success, type=connection)

        if on_failure is not None:
            self.failed.connect(self.on_failure, type=connection)

    def run(self, *args, **kwargs):
        try:
            result = self.target(*self.args, **self.kwargs)

        except Exception as e:
            error = traceback.format_exc()
            return self.failed.emit(e, error)

        else:
            self.succeeded.emit(result)


def iterable(arg):
    return (
        isinstance(arg, collections.Iterable)
        and not isinstance(arg, six.string_types)
    )


def open_file_location(fname):
    if os.path.exists(fname):
        if os.name == "nt":
            subprocess.Popen("explorer /select,%s" % fname)
        else:
            webbrowser.open(os.path.dirname(fname))
    else:
        raise OSError("%s did not exist" % fname)


def normpath(path):
    return os.path.normpath(
        os.path.abspath(path).replace("\\", "/")
    )


def normpaths(*paths):
    return list(map(normpath, paths))


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """Key for use with sorted(key=) and str.sort(key=)

    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)

    """

    return [atoi(c) for c in re.split(r'(\d+)', text)]
