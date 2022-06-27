# -*- coding: utf-8 -*-

"""Plotting interface."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------
import numpy as np

from .axes import Axes
from .base import BaseCanvas
from .interact import Grid, Boxed, Stacked, Lasso
from .panzoom import PanZoom
from .visuals import (
    ScatterVisual, UniformScatterVisual, PlotVisual, UniformPlotVisual,
    HistogramVisual, TextVisual, LineVisual, PolygonVisual,
    DEFAULT_COLOR)
from .transform import NDC
from phylib.utils._types import _as_tuple



#------------------------------------------------------------------------------
# Plotting interface
#------------------------------------------------------------------------------

class PlotCanvas(BaseCanvas):
    """Plotting canvas that supports different layouts, subplots, lasso, axes, panzoom."""

    _current_box_index = (0,)
    interact = None
    n_plots = 1
    has_panzoom = True
    has_axes = False
    has_lasso = False
    constrain_bounds = (-2, -2, +2, +2)
    _enabled = False

    def __init__(self, *args, **kwargs):
        super(PlotCanvas, self).__init__(*args, **kwargs)

    def _enable(self):
        """Enable panzoom, axes, and lasso if required."""
        self._enabled = True
        if self.has_panzoom:
            self.enable_panzoom()
        if self.has_axes:
            self.enable_axes()
        if self.has_lasso:
            self.enable_lasso()

    def set_layout(
            self, layout=None, shape=None, n_plots=None, origin=None,
            box_pos=None, has_clip=True):
        """Set the plot layout: grid, boxed, stacked, or None."""

        self.layout = layout

        # Constrain pan zoom.
        if layout == 'grid':
            self._current_box_index = (0, 0)
            self.grid = Grid(shape, has_clip=has_clip)
            self.grid.attach(self)
            self.interact = self.grid

        elif layout == 'boxed':
            self.n_plots = len(box_pos)
            self.boxed = Boxed(box_pos=box_pos)
            self.boxed.attach(self)
            self.interact = self.boxed

        elif layout == 'stacked':
            self.n_plots = n_plots
            self.stacked = Stacked(n_plots, origin=origin)
            self.stacked.attach(self)
            self.interact = self.stacked

        if layout == 'grid' and shape is not None:
            self.interact.add_boxes(self)

    def __getitem__(self, box_index):
        self._current_box_index = _as_tuple(box_index)
        return self

    @property
    def canvas(self):
        return self

    def add_visual(self, visual, *args, **kwargs):
        """Add a visual and possibly set some data directly.

        Parameters
        ----------

        visual : Visual
        clearable : True
            Whether the visual should be deleted when calling `canvas.clear()`.
        exclude_origins : list-like
            List of interact instances that should not apply to that visual. For example, use to
            add a visual outside of the subplots, or with no support for pan and zoom.
        key : str
            An optional key to identify a visual

        """
        if not self._enabled:
            self._enable()
        # The visual is not added again if it has already been added, in which case
        # the following call is a no-op.
        super(PlotCanvas, self).add_visual(
            visual,
            # Remove special reserved keywords from kwargs, which is otherwise supposed to
            # contain data for visual.set_data().
            clearable=kwargs.pop('clearable', True),
            key=kwargs.pop('key', None),
            exclude_origins=kwargs.pop('exclude_origins', ()),
        )
        self.update_visual(visual, *args, **kwargs)

    def update_visual(self, visual, *args, **kwargs):
        """Set the data of a visual, standalone or at the end of a batch."""
        if not self._enabled:  # pragma: no cover
            self._enable()
        # If a batch session has been initiated in the visual, add the data from the
        # visual's BatchAccumulator.
        if visual._acc.items:
            kwargs.update(visual._acc.data)
            # If the batch accumulator has box_index, we get it in kwargs now.
        # We remove the box_index before calling set_data().
        box_index = kwargs.pop('box_index', None)
        # If no data was obtained at this point, we return.
        if box_index is None and not kwargs:
            return visual
        # If kwargs is not empty, we set the data on the visual.
        data = visual.set_data(*args, **kwargs) if kwargs else None
        # Finally, we may need to set the box index.
        # box_index could be specified directly to add_visual, or it could have been
        # constructed in the batch, or finally it should just be the current box index
        # by default.
        if self.interact and data:
            box_index = box_index if box_index is not None else self._current_box_index
            visual.set_box_index(box_index, data=data)
        return visual

    # Plot methods
    #--------------------------------------------------------------------------

    def scatter(self, *args, **kwargs):
        """Add a standalone (no batch) scatter plot."""
        return self.add_visual(ScatterVisual(marker=kwargs.pop('marker', None)), *args, **kwargs)

    def uscatter(self, *args, **kwargs):
        """Add a standalone (no batch) uniform scatter plot."""
        return self.add_visual(UniformScatterVisual(
            marker=kwargs.pop('marker', None),
            color=kwargs.pop('color', None),
            size=kwargs.pop('size', None)), *args, **kwargs)

    def plot(self, *args, **kwargs):
        """Add a standalone (no batch) plot."""
        return self.add_visual(PlotVisual(), *args, **kwargs)

    def uplot(self, *args, **kwargs):
        """Add a standalone (no batch) uniform plot."""
        return self.add_visual(UniformPlotVisual(color=kwargs.pop('color', None)), *args, **kwargs)

    def lines(self, *args, **kwargs):
        """Add a standalone (no batch) line plot."""
        return self.add_visual(LineVisual(), *args, **kwargs)

    def text(self, *args, **kwargs):
        """Add a standalone (no batch) text plot."""
        return self.add_visual(TextVisual(color=kwargs.pop('color', None)), *args, **kwargs)

    def polygon(self, *args, **kwargs):
        """Add a standalone (no batch) polygon plot."""
        return self.add_visual(PolygonVisual(), *args, **kwargs)

    def hist(self, *args, **kwargs):
        """Add a standalone (no batch) histogram plot."""
        return self.add_visual(HistogramVisual(), *args, **kwargs)

    # Enable methods
    #--------------------------------------------------------------------------

    def enable_panzoom(self):
        """Enable pan zoom in the canvas."""
        self.panzoom = PanZoom(aspect=None, constrain_bounds=self.constrain_bounds)
        self.panzoom.attach(self)

    def enable_lasso(self):
        """Enable lasso in the canvas."""
        self.lasso = Lasso()
        self.lasso.attach(self)

    def enable_axes(self, data_bounds=None, show_x=True, show_y=True):
        """Show axes in the canvas."""
        self.axes = Axes(data_bounds=data_bounds, show_x=show_x, show_y=show_y)
        self.axes.attach(self)

