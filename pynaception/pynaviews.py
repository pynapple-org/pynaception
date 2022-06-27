# -*- coding: utf-8 -*-
# @Author: gviejo
# @Date:   2022-05-31 23:22:50
# @Last Modified by:   gviejo
# @Last Modified time: 2022-06-01 09:39:05

import gc
import numpy as np
# from .base import ManualClusteringView
from .plot.visuals import PlotVisual
from .raster import ScatterVisual
from plot import PlotCanvas


class PynaView(object):
    
    def __init__(self, **kwargs):
        self._closed = False

        # Attached GUI.
        self.gui = None

        # self.canvas = self.plot_canvas_class()
        self.canvas = PlotCanvas()

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



class TsdView(PynaView):


    def __init__(self, tsd, **kwargs):

        super(TsdView, self).__init__(**kwargs)

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
            color=[0.7, 0.8, 0.45, 1], 
            data_bounds = self.data_bounds,
            depth=np.array([10]))
        self._update_axes()
        self.canvas.update()

    def attach(self, gui):
        """Attach the view to the GUI."""
        super(TsdView, self).attach(gui)

        #self.actions.add(self.increase_marker_size)
        #self.actions.add(self.decrease_marker_size)
        # self.actions.separator()



class TsGroupView(PynaView):
    """This view shows a raster plot of all clusters.

    Constructor
    -----------

    spike_times : array-like
        An `(n_spikes,)` array with the spike times, in seconds.
    spike_clusters : array-like
        An `(n_spikes,)` array with the spike-cluster assignments.
    cluster_ids : array-like
        The list of all clusters to show initially.

    """

    _default_position = 'right'

    default_shortcuts = {
        'change_marker_size': 'alt+wheel',
        'switch_color_scheme': 'shift+wheel',
        'decrease_marker_size': 'ctrl+shift+-',
        'increase_marker_size': 'ctrl+shift++',
        'select_cluster': 'ctrl+click',
        'select_more': 'shift+click',
    }

    def __init__(self, spike_times, spike_clusters, cluster_ids, **kwargs):
        self.spike_times = spike_times
        self.n_spikes = len(spike_times)
        self.duration = spike_times[-1] * 1.01
        self.n_clusters = 1

        assert len(spike_clusters) == self.n_spikes
        self.spike_clusters = spike_clusters
        self.all_cluster_ids = cluster_ids
        self.n_clusters = len(self.all_cluster_ids)
        self.spike_ids = np.isin(self.spike_clusters, self.all_cluster_ids)

        super(TsGroupView, self).__init__(**kwargs)

        self.canvas.set_layout('stacked', origin='top', n_plots=self.n_clusters, has_clip=False)
        self.canvas.enable_axes()

        self.visual = ScatterVisual(
            marker='vbar',
            marker_scaling='''
                point_size = v_size * u_zoom.y + 5.;
                float width = 0.2;
                float height = 0.5;
                vec2 marker_size = point_size * vec2(width, height);
                marker_size.x = clamp(marker_size.x, 1, 20);
            ''',
        )
        self.visual.inserter.insert_vert('''
                gl_PointSize = a_size * u_zoom.y + 5.0;
        ''', 'end')
        self.canvas.add_visual(self.visual)
        self.canvas.panzoom.set_constrain_bounds((-1, -2, +1, +2))


    def _get_x(self):
        """Return the x position of the spikes."""
        return self.spike_times[self.spike_ids]

    def _get_y(self):
        """Return the y position of the spikes, given the relative position of the clusters."""
        return np.zeros(np.sum(self.spike_ids))

    def _index_of(self, arr, lookup):
        # Equivalent of np.digitize(arr, lookup) - 1, but much faster.
        # TODO: assertions to disable in production for performance reasons.
        # TODO: np.searchsorted(lookup, arr) is faster on small arrays with large
        # values
        lookup = np.asarray(lookup, dtype=np.int32)
        m = (lookup.max() if len(lookup) else 0) + 1
        tmp = np.zeros(m + 1, dtype=int)
        # Ensure that -1 values are kept.
        tmp[-1] = -1
        if len(lookup):
            tmp[lookup] = np.arange(len(lookup))
        return tmp[arr]

    def _get_box_index(self):
        """Return, for every spike, its row in the raster plot. This depends on the ordering
        in self.cluster_ids."""
        cl = self.spike_clusters[self.spike_ids]
        # Sanity check.
        # assert np.all(np.in1d(cl, self.cluster_ids))
        return self._index_of(cl, self.all_cluster_ids)

    def _get_color(self, box_index):
        """Return, for every spike, its color, based on its box index."""
        cluster_colors = np.random.rand(len(self.all_cluster_ids), 4)
        cluster_colors[:,-1] = 1.0

        return cluster_colors[box_index, :]

    # Main methods
    # -------------------------------------------------------------------------

    def _get_data_bounds(self):
        """Bounds of the raster plot view."""
        return (0, 0, self.duration, self.n_clusters)

    def update_cluster_sort(self, cluster_ids):
        """Update the order of all clusters."""
        self.all_cluster_ids = cluster_ids
        self.visual.set_box_index(self._get_box_index())
        self.canvas.update()

    def update_color(self):
        """Update the color of the spikes, depending on the selected clusters."""
        box_index = self._get_box_index()
        color = self._get_color(box_index, selected_clusters=self.cluster_ids)
        self.visual.set_color(color)
        self.canvas.update()

    @property
    def status(self):
        return 'Color scheme: %s' % self.color_scheme

    def plot(self, **kwargs):
        """Make the raster plot."""
        print(1)
        if not len(self.spike_clusters):
            return
        x = self._get_x()  # spike times for the selected spikes
        y = self._get_y()  # just 0
        box_index = self._get_box_index()
        color = self._get_color(box_index)
        assert x.shape == y.shape == box_index.shape
        assert color.shape[0] == len(box_index)
        self.data_bounds = self._get_data_bounds()

        self.visual.set_data(
            x=x, y=y, color=color, size=5,
            data_bounds=(0, -1, self.duration, 1))
        self.visual.set_box_index(box_index)
        self.canvas.stacked.n_boxes = self.n_clusters
        self._update_axes()
        # self.canvas.stacked.add_boxes(self.canvas)
        self.canvas.update()

    def attach(self, gui):
        """Attach the view to the GUI."""
        super(TsGroupView, self).attach(gui)

        #self.actions.add(self.increase_marker_size)
        #self.actions.add(self.decrease_marker_size)
        # self.actions.separator()

