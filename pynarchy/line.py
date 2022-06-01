# -*- coding: utf-8 -*-

"""Scatter view."""


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import numpy as np
from .base import ManualClusteringView
from .plot.visuals import PlotVisual


class LineView(ManualClusteringView):


    def __init__(self, tsd, **kwargs):

        super(LineView, self).__init__(**kwargs)

        self.tsd = tsd

        self.canvas.set_layout('stacked', n_plots=1)
        self.canvas.enable_axes()

        self.visual = PlotVisual()

        self.canvas.add_visual(self.visual)
        
        self.data_bounds = np.array([[
            tsd.index.values.min(), 
            tsd.values.min(), 
            tsd.index.values.max(),
            tsd.values.max()]
            ])


    def plot(self, **kwargs):        
        self.visual.set_data(
            x=self.tsd.index.values, 
            y=self.tsd.values, 
            color=np.ones(4), 
            data_bounds = self.data_bounds,
            depth=np.array([10]))
        self._update_axes()
        self.canvas.update()

    def attach(self, gui):
        """Attach the view to the GUI."""
        super(LineView, self).attach(gui)

        #self.actions.add(self.increase_marker_size)
        #self.actions.add(self.decrease_marker_size)
        # self.actions.separator()

