# -*- coding: utf-8 -*-
# @Author: gviejo
# @Date:   2022-06-01 15:14:19
# @Last Modified by:   gviejo
# @Last Modified time: 2022-06-21 16:52:47

from PyQt5.QtWidgets import QMainWindow, QApplication, QDockWidget, QListWidget, QTextEdit, QVBoxLayout
import sys
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui
from PyQt5.QtCore import Qt

import numpy as np

from vispy.scene import SceneCanvas
from vispy.scene.visuals import Markers, Line


class DockDialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = "PyQt5 StackedWidget"
        self.top = 200
        self.left = 500
        self.width = 400    
        self.height = 300
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        # self.createDockWidget()

        self.canvas = SceneCanvas(self, keys='interactive', show=True)
        self.viewbox = self.canvas.central_widget.add_grid().add_view(row=0, col=0, camera='panzoom')

        self.lines = Line(
            pos=np.random.rand(10,2), 
            color=np.random.rand(4),
            method='gl', 
            width=0.5, 
            connect='segments')

        self.viewbox.add(self.lines)


        dock = QDockWidget("Dockable", self)
        
        dock.setWidget(self.viewbox)
        
        self.addDockWidget(Qt.LeftDockWidgetArea, dock, Qt.Horizontal)


        # layout = QVBoxLayout(self)
        # layout.setContentsMargins(0,0,0,0)
        # layout.addWidget(self.canvas.native, 1)

        self.show()
 
    def createDockWidget(self):
        menubar = self.menuBar()
        file = menubar.addMenu("File")
        file.addAction("New")
        file.addAction("Save")
        file.addAction("Close")
        self.dock = QDockWidget("Dockable", self)
        self.listWiget = QListWidget()
        list = ["Python", "C++", "Java", "C#"]
        self.listWiget.addItems(list)
        self.dock.setWidget(self.listWiget)
        self.dock.setFloating(False)
        self.setCentralWidget(QTextEdit())
        self.addDockWidget(Qt.TopDockWidgetArea, self.dock)
 


 
App = QApplication(sys.argv)
window = DockDialog()
sys.exit(App.exec())