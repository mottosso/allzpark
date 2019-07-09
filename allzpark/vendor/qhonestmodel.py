import os
import sys
import logging
import itertools
import traceback
import collections

from Qt import QtCore, QtCompat

PY2 = sys.version_info[0] == 2

# Disable threading, to simplify debugging
USE_THREADING = not bool(os.getenv("QHONESTMODEL_NO_THREADING"))

_log = logging.getLogger(__name__)
_basestring = basestring if PY2 else str  # For Python 2/3
_usercount = itertools.count(1)
_threads = []


try:
    from queue import Queue
except ImportError:
    # Python 2
    from Queue import Queue


def UserRole():
    """Guarantee unique indices per user role"""
    return QtCore.Qt.UserRole + next(_usercount)


# Roles
DisplayRole = QtCore.Qt.DisplayRole
EditRole = QtCore.Qt.EditRole
IconRole = QtCore.Qt.DecorationRole
MadeRole = UserRole()
HasFetchedRole = UserRole()
LoadedRole = UserRole()
CurrentRowRole = UserRole()
Finish = None


class QHonestListModel(QtCore.QAbstractListModel):
    pass


class QHonestTableModel(QtCore.QAbstractTableModel):
    pass


class QHonestTreeModel(QtCore.QAbstractItemModel):
    """Model capable of making promises

    A QPromiseItem is an item that hasn't yet been populated with data.
    For example, a request for data off disk that take between
    seconds to minutes can be represented by a promise that this
    data is on the way.

    Promises are lazily fulfilled, in that they are not acted upon
    until the data is requested. This helps reduce load, increase
    performance and enable virtually infinite sizes of data. Once
    a promise has been fulfilled, it is removed from the model and
    replaced with the actual data which then acts as a cache for
    future queries.

    """

    promiseFulfilled = QtCore.Signal()

    def __init__(self, root=None, parent=None):
        super(QHonestTreeModel, self).__init__(parent)
        self._root = root

    def setRoot(self, root):
        self.beginResetModel()
        self._root = root
        self.endResetModel()

    def flags(self, index):
        if not index.isValid():
            return super(QHonestTreeModel, self).flags(index)

        item = index.internalPointer()
        return item.flags(index)

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()

        # Lazily fulfill promises
        if isinstance(item, QPromiseItem) and not item.made:
            promise = item
            promise.make(
                onSuccess=(
                    lambda child:
                    self.onPromiseFulfilled(promise, child)
                ),
                onFailure=(
                    lambda error:
                    self.onPromiseBroken(promise, error)
                ),
            )

        return item.data(role, index.column())

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        item = index.internalPointer()
        item.setData(value, role, index.column())
        QtCompat.dataChanged(self, index, index)

        return True

    def onPromiseFulfilled(self, promise, child):
        parent = promise.parent() or self._root
        parentIndex = self.createIndex(0, 0, parent)
        self.layoutAboutToBeChanged.emit()

        # Remove promise on finish
        if child is Finish:
            self.removeChild(parentIndex, promise)

            # Special case of a promise not delivering any items
            if not parent.childCount():
                self.appendChild(parentIndex, QHonestItem("Empty"))

            self.layoutChanged.emit()
            self.promiseFulfilled.emit()
            return

        self.insertChild(parentIndex, promise.row(), child)
        self.layoutChanged.emit()

    def onPromiseBroken(self, promise, error):
        parent = promise.parent() or self._root
        index = self.createIndex(0, 0, parent)
        self.layoutAboutToBeChanged.emit()

        # Remove promise on finish
        self.removeChild(index, promise)
        self.appendChild(index, QHonestItem("Failed.."))
        self.layoutChanged.emit()
        self.promiseFulfilled.emit()

    def appendChild(self, index, child):
        item = index.internalPointer()
        row = item.childCount()
        self.beginInsertRows(index, row, row)
        item.appendChild(child)
        self.endInsertRows()
        QtCompat.dataChanged(self, index, index)

    def insertChild(self, index, row, child):
        item = index.internalPointer()

        if row < 0:
            row = item.childCount() + row

        self.beginInsertRows(index, row, row)
        item.insertChild(row, child)
        self.endInsertRows()
        QtCompat.dataChanged(self, index, index)

    def removeChild(self, index, child):
        item = index.internalPointer()
        last = child.row()
        self.beginRemoveRows(index, last, last)
        item.removeChild(child)
        self.endRemoveRows()
        QtCompat.dataChanged(self, index, index)

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            return None

        return str(section)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index=QtCore.QModelIndex()):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self._root:
            return QtCore.QModelIndex()

        if parentItem is None:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowItem(self, row=0, parent=QtCore.QModelIndex()):
        """Find child at `row` in `parent`

        Arguments:
            row (int, optional): Return child at this row, defaults to first
            parent (QtCore.QModelIndex): Return child of this parent

        Returns (QHonestItem or None): The child if found

        """

        assert isinstance(row, int), "%s must be of type int" % row
        assert isinstance(parent, QtCore.QModelIndex), (
            "%s must be of type QtCore.QModelIndex" % parent)

        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = parent.internalPointer()

        try:
            return parentItem.child(row)
        except IndexError:
            return None

    def row(self, row=0, parent=QtCore.QModelIndex()):
        try:
            item = self.rowItem(row, parent)
            return self.createIndex(0, 0, item)
        except AttributeError:
            return QtCore.QModelIndex()

    def findRowItems(self,
                     text,
                     column=0,
                     role=DisplayRole,
                     parent=QtCore.QModelIndex()):
        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = parent.internalPointer()

        for child in parentItem.children():
            if child.data(role, column) == text:
                yield child

    def findRowItem(self,
                    text,
                    column=0,
                    role=DisplayRole,
                    parent=QtCore.QModelIndex()):
        return next(self.findRowItems(text, column, role, parent), None)

    def findRow(self,
                text,
                column=0,
                role=DisplayRole,
                parent=QtCore.QModelIndex()):
        try:
            item = self.findRowItem(text, column, role, parent)
            return self.createIndex(0, 0, item)
        except AttributeError:
            return QtCore.QModelIndex()

    def findRows(self,
                 text,
                 column=0,
                 role=DisplayRole,
                 parent=QtCore.QModelIndex()):

        for item in self.findRowItems(text, column, role, parent):
            yield self.createIndex(0, 0, item)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            parentItem = self._root
        else:
            parentItem = parent.internalPointer()

        return parentItem.columnCount()


class QHonestItem(QtCore.QObject):
    def __init__(self, text):
        super(QHonestItem, self).__init__(parent=None)
        self._data = collections.defaultdict(dict)
        self._parent = None
        self._children = list()

        self.setData(text, DisplayRole, 0)
        self.setData("", DisplayRole, 1)
        self.setData(0, CurrentRowRole)

    def __str__(self):
        return self.data(DisplayRole)

    def __repr__(self):
        return "{module}.{type}<{name}>".format(
            module=self.__module__,
            type=type(self).__name__,
            name=self.data(DisplayRole)
        )

    def text(self, column=0):
        return self._data[DisplayRole][column]

    def flags(self, index):
        return (
            QtCore.Qt.ItemIsEnabled |
            QtCore.Qt.ItemIsSelectable
        )

    def data(self, role, column=0):
        if role not in self._data:
            return

        try:
            return self._data[role][column]

        except KeyError:
            # No such role
            pass

        except IndexError:
            # No such column
            pass

    def setData(self, value, role, column=0):
        self._data[role][column] = value

    def findChild(self, value, role=DisplayRole):
        pass

    def appendChild(self, item):
        assert isinstance(item, QHonestItem), (
            "item must be of type QHonestItem"
        )

        # Replace existing parent, if any
        parent = item._parent
        if parent not in (None, self):
            parent.removeChild(item)

        item._parent = self
        self._children.append(item)

    def insertChild(self, row, item):
        assert isinstance(item, QHonestItem), (
            "item must be of type QHonestItem"
        )

        # Replace existing parent, if any
        parent = item._parent
        if parent not in (None, self):
            parent.removeChild(item)

        item._parent = self
        self._children.insert(row, item)

    def removeChild(self, item):
        item._parent = None
        self._children.remove(item)

    def popChild(self, index):
        item = self._children.pop(index)
        item._parent = None
        return item

    def children(self):
        return self._children[:]

    def child(self, row):
        return self._children[row]

    def parent(self):
        return self._parent

    def childCount(self):
        return len(self._children)

    def columnCount(self):
        return len(self._data[DisplayRole])

    def row(self):
        return (
            self._parent._children.index(self)
            if self._parent else 0
        )

    @classmethod
    def from_json(cls, text, data="", sort=True):
        rootItem = cls(text)

        if isinstance(data, dict):
            items = sorted(data.items()) if sort else data.items()
            for key, value in items:
                child = cls.from_json(key, value)
                rootItem.appendChild(child)

        elif isinstance(data, list):
            for index, value in enumerate(data):
                child = cls.from_json(str(index), value)
                rootItem.appendChild(child)

        else:
            rootItem.setData(str(data), DisplayRole, 1)

        return rootItem


def default_success(parent, items):
    """Default success"""


def default_failure(error):
    """Default error"""
    _log.error(str(error))


class QPromiseItem(QHonestItem):
    """A placeholder for a future data"""

    def __init__(self, text, func, args=None, kwargs=None):
        super(QPromiseItem, self).__init__(text)

        self._func = func
        self._args = args or []
        self._kwargs = kwargs or {}
        self._result = Queue()

        self.made = False

    def make(self, onSuccess=None, onFailure=None):
        self.made = True

        def _onSuccess(*result):
            self._result.put(result)
            return (onSuccess or default_success)(*result)

        def _onFailure(*result):
            self._result.put(result)
            return (onFailure or default_failure)(*result)

        def _defer():
            defer(
                self._func,
                args=self._args,
                kwargs=self._kwargs,
                on_success=_onSuccess,
                on_failure=_onFailure,
            )

        delay(_defer, 10)

        return self

    def get(self):
        return self._result.get()

    def wait(self):
        self._result.get()


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
            if iterable(result):
                while True:

                    try:
                        value = next(result)

                    except StopIteration:
                        break

                    except Exception:
                        error = traceback.format_exc()
                        on_failure(error)
                        break

                    else:
                        on_success(value)
            else:
                on_success(result)


class Thread(QtCore.QThread):
    succeeded = QtCore.Signal(object)
    failed = QtCore.Signal(_basestring)

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
            return self.failed.emit(e)

        else:
            if iterable(result):
                while True:
                    try:
                        value = next(result)

                    except StopIteration:
                        break

                    except Exception:
                        error = traceback.format_exc()
                        self.failed.emit(error)
                        break

                    else:
                        self.succeeded.emit(value)

            else:
                self.succeeded.emit(result)


def iterable(arg):
    return (
        isinstance(arg, collections.Iterable)
        and not isinstance(arg, _basestring)
    )


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

