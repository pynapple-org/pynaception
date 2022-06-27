# -*- coding: utf-8 -*-
# @Author: gviejo
# @Date:   2022-05-26 23:23:55
# @Last Modified by:   gviejo
# @Last Modified time: 2022-06-01 21:39:54

from collections import defaultdict
from functools import partial
import logging

from .qt import (
    QApplication, QWidget, QDockWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QCheckBox,
    QMenu, QToolBar, QStatusBar, QMainWindow, QMessageBox, Qt, QPoint, QSize, _load_font,
    _wait, prompt, show_box, screenshot as make_screenshot)
from .state import GUIState, _gui_state_path, _get_default_state_path
from .actions import Actions, Snippets
from phylib.utils import emit, connect

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# GUI utils
# -----------------------------------------------------------------------------

def _try_get_matplotlib_canvas(view):
    """Get the Qt widget from a matplotlib figure."""
    try:
        from matplotlib.pyplot import Figure
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        if isinstance(view, Figure):
            view = FigureCanvasQTAgg(view)
        # Case where the view has a .figure property which is a matplotlib figure.
        elif isinstance(getattr(view, 'figure', None), Figure):
            view = FigureCanvasQTAgg(view.figure)
        elif isinstance(getattr(getattr(view, 'canvas', None), 'figure', None), Figure):
            view = FigureCanvasQTAgg(view.canvas.figure)
    except ImportError as e:  # pragma: no cover
        logger.warning("Import error: %s", e)
    return view


def _try_get_opengl_canvas(view):
    """Convert from QOpenGLWindow to QOpenGLWidget."""
    from plot.base import BaseCanvas
    if isinstance(view, BaseCanvas):
        print(3)
        return QWidget.createWindowContainer(view)
    elif isinstance(getattr(view, 'canvas', None), BaseCanvas):
        print(4)
        return QWidget.createWindowContainer(view.canvas)
    return view


def _widget_position(widget):  # pragma: no cover
    return widget.parentWidget().mapToGlobal(widget.geometry().topLeft())


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
    """A dock widget with a custom title bar.

    The title bar has a status text at the middle, and a group of buttons on the right.
    By default, the buttons on the right are screenshot and close. New buttons can be added
    in this group, from right to left.

    """

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

    def add_button(
            self, callback=None, text=None, icon=None, checkable=False,
            checked=False, event=None, name=None):
        """Add a button to the dock title bar, to the right.

        Parameters
        ----------

        callback : function
            Callback function when the button is clicked.
        text : str
            Text of the button.
        icon : str
            Fontawesome icon of the button specified as a unicode string with 4 hexadecimal
            characters.
        checkable : boolean
            Whether the button is checkable.
        checked : boolean
            Whether the checkable button is initially checked.
        event : str
            Name of the event that is externally raised when the status of the button is changed.
            This is used to synchronize the button's checked status when the value changes
            via another mean than clicking on the button.
        name : str
            Name of the button.

        """
        if callback is None:
            return partial(
                self.add_button, text=text, icon=icon, name=name,
                checkable=checkable, checked=checked, event=event)

        name = name or getattr(callback, '__name__', None) or text
        assert name
        button = QPushButton(chr(int(icon, 16)) if icon else text)
        if self._font:
            button.setFont(self._font)
        button.setCheckable(checkable)
        if checkable:
            button.setChecked(checked)
        button.setToolTip(name)

        if callback:
            @button.clicked.connect
            def on_clicked(state):
                return callback(state)

        # Change the state of the button when this event is called.
        if event:
            @connect(event=event, sender=self.view)
            def on_state_changed(sender, checked):
                button.setChecked(checked)

        assert name not in self._dock_widgets
        self._dock_widgets[name] = button
        self._buttons_layout.addWidget(button, 1)

        return button

    def add_checkbox(self, callback=None, text=None, checked=False, name=None):
        """Add a checkbox to the dock title bar, to the right.

        Parameters
        ----------

        callback : function
            Callback function when the checkbox is clicked.
        text : str
            Text of the checkbox.
        checked : boolean
            Whether the checkbox is initially checked.
        name : str
            Name of the button.

        """
        if callback is None:
            return partial(self.add_checkbox, text=text, checked=checked, name=name)

        name = name or getattr(callback, '__name__', None) or text
        assert name
        checkbox = QCheckBox(text)
        checkbox.setLayoutDirection(2)
        checkbox.setToolTip(name)
        if checked:
            checkbox.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        if callback:
            @checkbox.stateChanged.connect
            def on_state_changed(state):
                return callback(state == Qt.Checked)

        assert name not in self._dock_widgets
        self._dock_widgets[name] = checkbox
        self._buttons_layout.addWidget(checkbox, 1)

        return checkbox

    def get_widget(self, name):
        """Get a dock title bar widget by its name."""
        return self._dock_widgets[name]

    @property
    def status(self):
        """Current status text of the title bar."""
        return self._status.text()

    def set_status(self, text):
        """Set the status text of the widget."""
        n = self.max_status_length
        if len(text) >= n:
            text = text[:n // 2] + ' ... ' + text[-n // 2:]
        self._status.setText(text)

    def _default_buttons(self):
        """Create the default buttons on the right."""

        # Only show the close button if the dock widget is closable.
        if int(self.features()) % 2 == 1:
            # Close button.
            @self.add_button(name='close', text='✕')
            def on_close(e):  # pragma: no cover
                if not self.confirm_before_close_view or show_box(
                    prompt(
                        "Close %s?" % self.windowTitle(),
                        buttons=['yes', 'no'], title='Close?')) == 'yes':
                    self.close()

        # Screenshot button.
        @self.add_button(name='screenshot', icon='f030')
        def on_screenshot(e):  # pragma: no cover
            if hasattr(self.view, 'screenshot'):
                self.view.screenshot()
            else:
                make_screenshot(self.view)

        # View menu button.
        @self.add_button(name='view_menu', icon='f0c9')
        def on_view_menu(e):  # pragma: no cover
            # Display the view menu.
            button = self._dock_widgets['view_menu']
            x = _widget_position(button).x()
            y = _widget_position(self._widget).y()
            self._menu.exec(QPoint(x, y))

    def _create_menu(self):
        """Create the contextual menu for this view."""
        self._menu = QMenu("%s menu" % self.objectName(), self)

    def _create_title_bar(self):
        """Create the title bar."""
        self._title_bar = QWidget(self)

        self._layout = QHBoxLayout(self._title_bar)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._title_bar.setStyleSheet(DOCK_TITLE_STYLESHEET)

        # Left part of the bar.
        # ---------------------

        # Widget name.
        label = QLabel(self.windowTitle())
        self._layout.addWidget(label)

        # Space.
        # ------
        self._layout.addStretch(1)

        # Buttons on the right.
        # ---------------------

        self._buttons = QWidget(self._title_bar)
        self._buttons_layout = QHBoxLayout(self._buttons)
        self._buttons_layout.setDirection(1)
        self._buttons_layout.setContentsMargins(0, 0, 0, 0)
        self._buttons_layout.setSpacing(1)
        self._buttons.setLayout(self._buttons_layout)

        # Add the default buttons.
        self._default_buttons()

        # Layout margin.
        self._layout.addWidget(self._buttons)
        self._title_bar.setLayout(self._layout)
        self.setTitleBarWidget(self._title_bar)

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

    dock._create_menu()
    dock._create_title_bar()
    dock._create_status_bar()

    return dock


def _get_dock_position(position):
    return {'left': Qt.LeftDockWidgetArea,
            'right': Qt.RightDockWidgetArea,
            'top': Qt.TopDockWidgetArea,
            'bottom': Qt.BottomDockWidgetArea,
            }[position or 'right']


def _prompt_save():  # pragma: no cover
    """Show a prompt asking the user whether he wants to save or not.

    Output is 'save', 'cancel', or 'close'

    """
    b = prompt(
        "Do you want to save your changes before quitting?",
        buttons=['save', 'cancel', 'close'], title='Save')
    return show_box(b)


def _remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
