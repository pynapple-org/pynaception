# -*- coding: utf-8 -*-

"""Qt dock window."""


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from collections import defaultdict
from functools import partial
import logging

from .qt import QMainWindow, QApplication, QMenu, QStatusBar, QToolBar, QSize, Qt
from .actions import Actions, Snippets
from .state import GUIState
from .widgets import _try_get_opengl_canvas, _try_get_matplotlib_canvas, _create_dock_widget, _get_dock_position

from phylib.utils import emit, connect



class GUI(QMainWindow):

    default_shortcuts = {
        'enable_snippet_mode': ':',
        'save': 'ctrl+s',
        'about': '?',
        'show_all_shortcuts': 'h',
        'exit': 'ctrl+q',
    }

    def __init__(self):
        # HACK to ensure that closeEvent is called only twice (seems like a
        # Qt bug).
        if not QApplication.instance():  # pragma: no cover
            raise RuntimeError("A Qt application must be created.")
        super(GUI, self).__init__()

        self.setDockOptions(QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)
        self.setAnimated(False)
        self.name = 'pynarchy'
        self.setWindowTitle(self.name)
        self.setObjectName(self.name)

        
        self.move(200, 200)
        self.resize(QSize(1200, 800))

        
        self.actions = []
        self._menus = {}
        ds = self.default_shortcuts
        self.file_actions = Actions(self, name='File', menu='&File', default_shortcuts=ds)

        # Views,
        self._views = []
        self._view_class_indices = defaultdict(int)  # Dictionary {view_name: next_usable_index}


        self.state = GUIState()

        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)

        self._toolbar = QToolBar('Toolbar', self)
        self._toolbar.setObjectName('Toolbar')
        self._toolbar.setIconSize(QSize(24,24))
        self._toolbar.hide()
        self.addToolBar(self._toolbar)

        self.snippets = Snippets(self)



    def get_menu(self, name, insert_before=None):
        """Get or create a menu."""
        if name not in self._menus:
            menu = QMenu(name)
            if not insert_before:
                self.menuBar().addMenu(menu)
            else:
                self.menuBar().insertMenu(self.get_menu(insert_before).menuAction(), menu)
            self._menus[name] = menu
        return self._menus[name]

    # Status bar
    # -------------------------------------------------------------------------

    @property
    def status_message(self):
        """The message in the status bar, can be set by the user."""
        return str(self._status_bar.currentMessage())

    @status_message.setter
    def status_message(self, value):
        if self._lock_status:
            return
        self._status_bar.showMessage(str(value))

    def lock_status(self):
        """Lock the status bar."""
        self._lock_status = True

    def unlock_status(self):
        """Unlock the status bar."""
        self._lock_status = False


    def add_view(self, view, position=None, closable=True, floatable=True, floating=None):
        """Add a dock widget to the main window.

        Parameters
        ----------

        view : View
        position : str
            Relative position where to add the view (left, right, top, bottom).
        closable : boolean
            Whether the view can be closed by the user.
        floatable : boolean
            Whether the view can be detached from the main GUI.
        floating : boolean
            Whether the view should be added in floating mode or not.

        """        

        name = self._set_view_name(view)
        self._views.append(view)
        self._view_class_indices[view.__class__] += 1

        # Get the Qt canvas for matplotlib/OpenGL views.
        widget = _try_get_matplotlib_canvas(view)
        widget = _try_get_opengl_canvas(widget)
        

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
