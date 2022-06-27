# -*- coding: utf-8 -*-
# @Author: gviejo
# @Date:   2022-05-26 16:11:25
# @Last Modified by:   gviejo
# @Last Modified time: 2022-06-01 18:06:05


from .qt import QWidget, QDockWidget, Qt, QSize, QHBoxLayout, QLabel, QVBoxLayout
from PyQt5.QtWidgets import QListWidget
import pynapple as nap
# from .raster import RasterView
# from .line import LineView

from .pynaviews import TsGroupView, TsdView

import numpy as np

DOCK_TITLE_STYLESHEET = '''
    * {
        padding: 0;
        margin: 0;
        border: 0;
        background: #272822;
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
        background: #272822;
        color: white;
    }

    QLabel {
        padding: 3px;
    }
'''
DOCK_LIST_STYLESHEET = '''
    * {
        border : 2px solid black;
        background : #272822;
        color : #F8F8F2;
        selection-color : yellow;
        selection-background-color : #E69F66;
    }
    
    QListView {
        background-color : #272822;

    }
'''



class Controller(QDockWidget):

    def __init__(self, pynavar, gui, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.pynavar = pynavar
        self.gui = gui
        self.views = {}

        self.setObjectName('Variables')
        self.setWindowTitle('Variables')
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.setAllowedAreas(Qt.LeftDockWidgetArea)

        self.listWidget=QListWidget()
        for k in pynavar.keys():
            if k != 'data':
                self.listWidget.addItem(k)

        self.listWidget.itemDoubleClicked.connect(self.select_view)
        self.listWidget.setStyleSheet(DOCK_LIST_STYLESHEET)
        self.setWidget(self.listWidget)
        self.setFixedWidth(self.listWidget.sizeHintForColumn(0)+40)

        self.gui.addDockWidget(Qt.LeftDockWidgetArea, self, Qt.Horizontal)

        self._create_title_bar()
        # self._create_status_bar()


    def select_view(self, item):
        var = self.pynavar[item.text()]

        if isinstance(var, nap.TsGroup):
            self.add_raster_view(var, item.text())
        elif isinstance(var, nap.Tsd):
            self.add_tsd_view(var, item.text())
        elif isinstance(var, nap.tsdframe):
            self.add_tsdframe_view(var, item.text())
            
        return

    def add_raster_view(self, tsgroup, name):
        group_times = np.hstack([tsgroup[k].index.values for k in tsgroup.keys()])
        group_clusters = np.hstack([
            np.ones(len(tsgroup[k]), dtype='int')*k for k in tsgroup.keys()
            ])
        cluster_ids = np.unique(group_clusters)

        view = TsGroupView(group_times, group_clusters, cluster_ids=cluster_ids)
        view.plot()
        view.attach(self.gui)
        self.views[name] = view
        return

    def add_tsd_view(self, tsd, name):
        view = TsdView(tsd)
        view.plot()
        view.attach(self.gui)
        self.views[name] = view
        return

    def add_tsdframe_view(self, tsdframe, name):
        print("TODO")
        return


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

        # Layout margin.
        self._title_bar.setLayout(self._layout)
        self.setTitleBarWidget(self._title_bar)

    def _create_status_bar(self):
        # Dock has requested widget and status bar.
        widget_container = QWidget(self)
        widget_layout = QVBoxLayout(widget_container)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(0)

        widget_layout.addWidget(self.listWidget, 100)

        # Widget status text.
        self._status = QLabel('')
        self._status.setMaximumHeight(30)
        self._status.setStyleSheet(DOCK_STATUS_STYLESHEET)
        widget_layout.addWidget(self._status, 1)

        widget_container.setLayout(widget_layout)
        self.setWidget(widget_container)