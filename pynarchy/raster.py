# -*- coding: utf-8 -*-

"""Scatter view."""


# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import numpy as np
from .base import ManualClusteringView

from .plot.base import BaseVisual
from .plot.utils import (
    _tesselate_histogram, _get_texture, _get_array, _get_pos, _get_index)
from phylib.utils.geometry import _get_data_bounds
from phylib.utils import Bunch

DEFAULT_COLOR = (0.03, 0.57, 0.98, .75)
"""Bounds in Normalized Device Coordinates (NDC)."""
NDC = (-1.0, -1.0, +1.0, +1.0)








class ScatterVisual(BaseVisual):
    """Scatter visual, displaying a fixed marker at various positions, colors, and marker sizes.

    Constructor
    -----------

    marker : string (used for all points in the scatter visual)
        Default: disc. Can be one of: arrow, asterisk, chevron, clover, club, cross, diamond,
        disc, ellipse, hbar, heart, infinity, pin, ring, spade, square, tag, triangle, vbar

    Parameters
    ----------

    x : array-like (1D)
    y : array-like (1D)
    pos : array-like (2D)
    color : array-like (2D, shape[1] == 4)
    size : array-like (1D)
        Marker sizes, in pixels
    depth : array-like (1D)
    data_bounds : array-like (2D, shape[1] == 4)

    """
    _init_keywords = ('marker',)
    default_marker_size = 10.
    default_marker = 'disc'
    default_color = DEFAULT_COLOR
    _supported_markers = (
        'arrow',
        'asterisk',
        'chevron',
        'clover',
        'club',
        'cross',
        'diamond',
        'disc',
        'ellipse',
        'hbar',
        'heart',
        'infinity',
        'pin',
        'ring',
        'spade',
        'square',
        'tag',
        'triangle',
        'vbar',
    )

    def __init__(self, marker=None, marker_scaling=None):
        super(ScatterVisual, self).__init__()

        # Set the marker type.
        self.marker = marker or self.default_marker
        assert self.marker in self._supported_markers

        self.set_shader('scatter')
        marker_scaling = marker_scaling or 'float marker_size = v_size;'
        self.fragment_shader = self.fragment_shader.replace('%MARKER_SCALING', marker_scaling)
        self.fragment_shader = self.fragment_shader.replace('%MARKER', self.marker)
        self.set_primitive_type('points')
        self.set_data_range(NDC)

    def vertex_count(self, x=None, y=None, pos=None, **kwargs):
        """Number of vertices for the requested data."""
        return y.size if y is not None else len(pos)

    def validate(
            self, x=None, y=None, pos=None, color=None, size=None, depth=None,
            data_bounds=None, **kwargs):
        """Validate the requested data before passing it to set_data()."""
        if pos is None:
            x, y = _get_pos(x, y)
            pos = np.c_[x, y]
        pos = np.asarray(pos)
        assert pos.ndim == 2
        assert pos.shape[1] == 2
        n = pos.shape[0]

        # Validate the data.
        color = _get_array(color, (n, 4), ScatterVisual.default_color, dtype=np.float32)
        size = _get_array(size, (n, 1), ScatterVisual.default_marker_size)
        depth = _get_array(depth, (n, 1), 0)
        if data_bounds is not None:
            data_bounds = _get_data_bounds(data_bounds, pos)
            assert data_bounds.shape[0] == n

        return Bunch(
            pos=pos, color=color, size=size, depth=depth, data_bounds=data_bounds,
            _n_items=n, _n_vertices=n)

    def set_data(self, *args, **kwargs):
        """Update the visual data."""
        data = self.validate(*args, **kwargs)
        self.n_vertices = self.vertex_count(**data)
        if data.data_bounds is not None:
            self.data_range.from_bounds = data.data_bounds
            pos_tr = self.transforms.apply(data.pos)
        else:
            pos_tr = data.pos
        pos_tr = np.c_[pos_tr, data.depth]
        self.program['a_position'] = pos_tr.astype(np.float32)
        self.program['a_size'] = data.size.astype(np.float32)
        self.program['a_color'] = data.color.astype(np.float32)
        self.emit_visual_set_data()
        return data

    def set_color(self, color):
        """Change the color of the markers."""
        color = _get_array(color, (self.n_vertices, 4), ScatterVisual.default_color)
        self.program['a_color'] = color.astype(np.float32)

    def set_marker_size(self, marker_size):
        """Change the size of the markers."""
        size = _get_array(marker_size, (self.n_vertices, 1))
        assert np.all(size > 0)
        self.program['a_size'] = size.astype(np.float32)


# -----------------------------------------------------------------------------
# Raster view
# -----------------------------------------------------------------------------

# class RasterView(ManualClusteringView):
class RasterView(ManualClusteringView):
#class RasterView(BaseColorView, BaseGlobalView, ManualClusteringView):
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

        super(RasterView, self).__init__(**kwargs)

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
        super(RasterView, self).attach(gui)

        #self.actions.add(self.increase_marker_size)
        #self.actions.add(self.decrease_marker_size)
        # self.actions.separator()

