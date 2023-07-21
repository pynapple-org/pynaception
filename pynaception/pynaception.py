# -*- coding: utf-8 -*-
# @Author: gviejo
# @Date:   2022-05-31 22:40:08
# @Last Modified by:   Guillaume Viejo
# @Last Modified time: 2023-07-21 18:11:43

import sys

from .gui import GUI
from .controller import Controller


######### QT @@@@@@@@@@@@@@@@@@@@@@@@@@
# from OpenGL import GL  # noqa

from PyQt5.QtWidgets import QApplication

# ######### SDL2 @@@@@@@@@@@@@@@@@@@@@@@
# import sdl2.ext
# import sdl2



def get_pynapple_variables(variables):
    tmp = variables.copy()
    pynavar = {}
    for k, v in tmp.items():
        if hasattr(v, '__module__'):
            if "pynapple" in v.__module__ and k[0] != '_':
                pynavar[k] = v

    return pynavar


def scope(variables):
    pynavar = get_pynapple_variables(variables)
    
    global QT_APP
    QT_APP = QApplication.instance()
    if QT_APP is None:  # pragma: no cover
        QT_APP = QApplication(sys.argv)


    gui = GUI()

    control = Controller(pynavar, gui)

    gui.show()

    QT_APP.exit(QT_APP.exec_())

    gui.close()

    return
