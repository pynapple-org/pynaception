# -*- coding: utf-8 -*-
# @Author: gviejo
# @Date:   2022-05-31 22:40:08
# @Last Modified by:   gviejo
# @Last Modified time: 2022-05-31 22:51:14


from .qt import create_app, run_app, Qt
from .gui import GUI
from .controller import Controller



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
    
    create_app()

    gui = GUI()

    control = Controller(pynavar, gui)

    gui.show()

    run_app()

    gui.close()

    return
