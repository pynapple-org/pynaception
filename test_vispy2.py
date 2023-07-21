# -*- coding: utf-8 -*-
# Copyright (c) Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
"""
This example shows how to retrieve event information from a callback.
You should see information displayed for any event you triggered.
"""

from PyQt5.QtWidgets import (QMainWindow,QTextEdit,QAction,QFileDialog,QApplication,qApp)
from PyQt5 import QtGui,QtCore,QtWidgets
#from numpy_stl import mesh
from vispy.app import timer, backends
from vispy import app
from vispy.scene import visuals, SceneCanvas
from vispy.scene.widgets import ViewBox


app.create()
w = QtWidgets.QWidget()
w.show()
app.run()
