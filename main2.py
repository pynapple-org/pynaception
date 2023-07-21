# -*- coding: utf-8 -*-
# @Author: gviejo
# @Date:   2022-06-01 22:04:59
# @Last Modified by:   gviejo
# @Last Modified time: 2022-06-05 21:24:57

from pynarchy.qt import create_app, run_app, Qt, QWidget, QDockWidget, Qt
from pynarchy.gui import GUI
from pynarchy.controller import Controller
from pynarchy.widgets import DockWidget
from pynarchy.plot.visuals import PlotVisual
# from plot import PlotCanvas

from vispy import app, gloo

from PyQt5.QtWidgets import QListWidget


from OpenGL import GL  # noqa
from PyQt5.QtGui import QOpenGLWindow

import numpy as np


create_app()

gui = GUI()



# # TsdView
# canvas = PlotCanvas()

# class BaseCanvas(QOpenGLWindow):
# 	def __init__(self, *args, **kwargs):
# 		super(BaseCanvas, self).__init__(*args, **kwargs)


# canvas = BaseCanvas()

# visual = PlotVisual()


# canvas.add_visual(visual)

# visual.set_data(x=np.random.rand(10),y=np.random.rand(10),color=[0.7, 0.8, 0.45, 1],
# 	data_bounds=[0,0,1,1], depth = [10])

# canvas.axes.reset_data_bounds([0,0,1,1])

# canvas.update()

from vispy.app.qt import QtSceneCanvas

canvas = QtCanvas()



# gui.add_view
widget = QWidget.createWindowContainer(canvas)


dock = QDockWidget("Dockable", gui)

listWiget = QListWidget()
listWiget.addItems(["Python", "C++", "Java", "C#"])
dock.setWidget(widget)
gui.addDockWidget(Qt.LeftDockWidgetArea, dock, Qt.Horizontal)


gui.show()


run_app()

gui.close()
