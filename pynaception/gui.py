# -*- coding: utf-8 -*-

"""Qt dock window."""


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from collections import defaultdict

from .qt import QMainWindow, QApplication, QMenu, QStatusBar, QToolBar, QSize, Qt, QWidget
from .qt import (
    QApplication, QWidget, QDockWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QCheckBox,
    QMenu, QToolBar, QStatusBar, QMainWindow, QMessageBox, Qt, QPoint, QSize, _load_font,
    _wait, prompt, show_box, screenshot as make_screenshot)

from contextlib import contextmanager
import string
import re
from functools import partial


class EventEmitter(object):
    """Singleton class that emits events and accepts registered callbacks.

    Example
    -------

    ```python
    class MyClass(EventEmitter):
        def f(self):
            self.emit('my_event', 1, key=2)

    o = MyClass()

    # The following function will be called when `o.f()` is called.
    @o.connect
    def on_my_event(arg, key=None):
        print(arg, key)

    ```

    """

    def __init__(self):
        self.reset()
        self.is_silent = False

    def set_silent(self, silent):
        """Set whether to silence the events."""
        self.is_silent = silent

    def reset(self):
        """Remove all registered callbacks."""
        self._callbacks = []

    def _get_on_name(self, func):
        """Return `eventname` when the function name is `on_<eventname>()`."""
        r = re.match("^on_(.+)$", func.__name__)
        if r:
            event = r.group(1)
        else:
            raise ValueError("The function name should be "
                             "`on_<eventname>`().")
        return event

    @contextmanager
    def silent(self):
        """Prevent all callbacks to be called if events are raised
        in the context manager.
        """
        self.is_silent = not(self.is_silent)
        yield
        self.is_silent = not(self.is_silent)

    def connect(self, func=None, event=None, sender=None, **kwargs):
        """Register a callback function to a given event.

        To register a callback function to the `spam` event, where `obj` is
        an instance of a class deriving from `EventEmitter`:

        ```python
        @obj.connect(sender=sender)
        def on_spam(sender, arg1, arg2):
            pass
        ```

        This is called when `obj.emit('spam', sender, arg1, arg2)` is called.

        Several callback functions can be registered for a given event.

        The registration order is conserved and may matter in applications.

        """        
        if func is None:
            return partial(self.connect, event=event, sender=sender, **kwargs)

        # Get the event name from the function.
        if event is None:
            event = self._get_on_name(func)

        # We register the callback function.
        self._callbacks.append((event, sender, func, kwargs))

        return func

    def unconnect(self, *items):
        """Unconnect specified callback functions or senders."""
        self._callbacks = [
            (event, sender, f, kwargs)
            for (event, sender, f, kwargs) in self._callbacks
            if f not in items and sender not in items and
            getattr(f, '__self__', None) not in items]

    def emit(self, event, sender, *args, **kwargs):
        """Call all callback functions registered with an event.

        Any positional and keyword arguments can be passed here, and they will
        be forwarded to the callback functions.

        Return the list of callback return results.

        """
        if self.is_silent:
            return
        sender_name = sender.__class__.__name__
        # Call the last callback if this is a single event.
        single = kwargs.pop('single', None)
        res = []
        # Put `last=True` callbacks at the end.
        callbacks = [c for c in self._callbacks if not c[-1].get('last', None)]
        callbacks += [c for c in self._callbacks if c[-1].get('last', None)]
        for e, s, f, k in callbacks:
            if e == event and (s is None or s == sender):
                f_name = getattr(f, '__qualname__', getattr(f, '__name__', str(f)))
                s_name = s.__class__.__name__                
                res.append(f(sender, *args, **kwargs))
                if single:
                    return res[-1]
        return res

_EVENT = EventEmitter()

emit = _EVENT.emit
connect = _EVENT.connect
unconnect = _EVENT.unconnect
silent = _EVENT.silent
set_silent = _EVENT.set_silent
reset = _EVENT.reset

# -----------------------------------------------------------------------------
# Dock widget
# -----------------------------------------------------------------------------

DOCK_TITLE_STYLESHEET = '''
    * {
        padding: 0;
        margin: 0;
        border: 0;
        background: #232426;
        color: white;
    }

    QPushButton {
        padding: 4px;
        margin: 0 1px;
    }

    QCheckBox {
        padding: 2px 4px;
        margin: 0 1px;
    }

    QLabel {
        padding: 3px;
    }

    QPushButton:hover, QCheckBox:hover {
        background: #323438;
    }

    QPushButton:pressed {
        background: #53575e;
    }

    QPushButton:checked {
        background: #6c717a;
    }
'''


DOCK_STATUS_STYLESHEET = '''
    * {
        padding: 0;
        margin: 0;
        border: 0;
        background: black;
        color: white;
    }

    QLabel {
        padding: 3px;
    }
'''


class DockWidget(QDockWidget):

    confirm_before_close_view = False
    max_status_length = 64

    def __init__(self, *args, widget=None, **kwargs):
        super(DockWidget, self).__init__(*args, **kwargs)
        # Load the font awesome font.
        # self._font = _load_font('fa-solid-900.ttf')
        self._font = None
        self._dock_widgets = {}
        self._widget = widget

    def closeEvent(self, e):
        """Qt slot when the window is closed."""
        emit('close_dock_widget', self)
        super(DockWidget, self).closeEvent(e)

    def _create_status_bar(self):
        # Dock has requested widget and status bar.
        widget_container = QWidget(self)
        widget_layout = QVBoxLayout(widget_container)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(0)

        widget_layout.addWidget(self._widget, 100)

        # Widget status text.
        self._status = QLabel('')
        self._status.setMaximumHeight(30)
        self._status.setStyleSheet(DOCK_STATUS_STYLESHEET)
        widget_layout.addWidget(self._status, 1)

        widget_container.setLayout(widget_layout)
        self.setWidget(widget_container)

def _get_dock_position(position):
    return {'left': Qt.LeftDockWidgetArea,
            'right': Qt.RightDockWidgetArea,
            'top': Qt.TopDockWidgetArea,
            'bottom': Qt.BottomDockWidgetArea,
            }[position or 'right']

def _create_dock_widget(widget, name, closable=True, floatable=True):
    """Create a dock widget wrapping any Qt widget."""
    dock = DockWidget(widget=widget)
    dock.setObjectName(name)
    dock.setWindowTitle(name)

    # Set gui widget options.
    options = QDockWidget.DockWidgetMovable
    if closable:
        options = options | QDockWidget.DockWidgetClosable
    if floatable:
        options = options | QDockWidget.DockWidgetFloatable

    dock.setFeatures(options)
    dock.setAllowedAreas(
        Qt.LeftDockWidgetArea |
        Qt.RightDockWidgetArea |
        Qt.TopDockWidgetArea |
        Qt.BottomDockWidgetArea
    )

    dock._create_status_bar()

    return dock

class GUI(QMainWindow):


    def __init__(self):
        # HACK to ensure that closeEvent is called only twice (seems like a
        # Qt bug).
        if not QApplication.instance():  # pragma: no cover
            raise RuntimeError("A Qt application must be created.")
        super(GUI, self).__init__()

        self.setDockOptions(QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)
        self.setAnimated(False)
        self.name = 'pynaception'
        self.setWindowTitle(self.name)
        self.setObjectName(self.name)

        
        self.move(200, 200)
        self.resize(QSize(1200, 800))

        
        self.actions = []
        self._menus = {}

        # Views,
        self._views = []
        self._view_class_indices = defaultdict(int)  # Dictionary {view_name: next_usable_index}


    def add_view(self, view, position=None, closable=True, floatable=True, floating=None):
        name = self._set_view_name(view)
        self._views.append(view)
        self._view_class_indices[view.__class__] += 1

        widget = QWidget.createWindowContainer(view.canvas)

        dock = _create_dock_widget(widget, name, closable=closable, floatable=floatable)
        self.addDockWidget(_get_dock_position(position), dock, Qt.Horizontal)

        if floating is not None:
            dock.setFloating(floating)
        dock.view = view
        view.dock = dock

        # Emit the close_view event when the dock widget is closed.
        @connect(sender=dock)
        def on_close_dock_widget(sender):
            self._views.remove(view)
            emit('close_view', view, self)

        dock.show()
        
        return dock

    def _set_view_name(self, view):
        """Set a unique name for a view: view class name, followed by the view index."""
        assert view not in self._views
        # Get all views of the same class.
        cls = view.__class__
        basename = cls.__name__
        views = self.list_views(view.__class__)
        if not views:
            # If the view is the first of its class, just use the base name.
            name = basename
        else:
            # index is the next usable index for the view's class.
            index = self._view_class_indices.get(cls, 0)
            assert index >= 1
            name = '%s (%d)' % (basename, index)
        view.name = name
        return name        

    def list_views(self, *classes):
        """Return the list of views which are instances of one or several classes."""
        s = set(classes)
        return [
            view for view in self._views
            if s.intersection({view.__class__, view.__class__.__name__})]
