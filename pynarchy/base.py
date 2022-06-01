# -*- coding: utf-8 -*-
# @Author: gviejo
# @Date:   2022-05-27 14:55:33
# @Last Modified by:   gviejo
# @Last Modified time: 2022-05-31 20:35:23
# -*- coding: utf-8 -*-


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import gc

import numpy as np

from plot import PlotCanvas



class ManualClusteringView(object):
    """Base class for clustering views.

    """    
    _default_position = None
    plot_canvas_class = PlotCanvas

    def __init__(self, **kwargs):
        self._closed = False

        # Attached GUI.
        self.gui = None

        self.canvas = self.plot_canvas_class()

        # Attach the Qt events to this class, so that derived class
        # can override on_mouse_click() and so on.
        self.canvas.attach_events(self)

    def _update_axes(self):
        """Update the axes."""
        self.canvas.axes.reset_data_bounds(self.data_bounds)


    def plot(self, **kwargs):  # pragma: no cover
        """Update the view with the current cluster selection."""
        print(2)
        # bunchs = self.get_clusters_data()
        # self.data_bounds = self._get_data_bounds(bunchs)
        # for bunch in bunchs:
        #     self._plot_cluster(bunch)
        # self._update_axes()
        self.canvas.update()

    def attach(self, gui):
        """Attach the view to the GUI.
        """        
        gui.add_view(self, position=None)
        self.gui = gui

    def show(self):
        """Show the underlying canvas."""
        return self.canvas.show()

    def close(self):
        """Close the view."""
        if hasattr(self, 'dock'):
            return self.dock.close()
        self.canvas.close()
        self._closed = True
        unconnect(self)
        gc.collect(0)   


