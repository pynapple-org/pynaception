# -*- coding: utf-8 -*-
# @Author: guillaume
# @Date:   2022-05-14 22:36:45
# @Last Modified by:   gviejo
# @Last Modified time: 2022-05-25 17:51:15
import os, sys
from pathlib import Path

from phylib.io.model import TemplateModel, get_template_params

from template_controller import TemplateController


from qt import Qt, QApplication, QWidget, QMessageBox
from gui.gui import (GUI, Actions, _try_get_matplotlib_canvas,
                   _try_get_opengl_canvas)

from plot import BaseCanvas

from cluster.views.base import BaseColorView, ManualClusteringView



from gui import create_app, run_app



params_path = '/home/guillaume/pynapple/data/A8604-211122/params.py'


p = Path(params_path)
dir_path = p.parent


model = TemplateModel(**get_template_params(params_path))


qt_app = create_app()



controller = TemplateController(model=model, dir_path=dir_path)
# gui = controller.create_gui()


view_creator = {
     #'ClusterScatterView': controller.create_cluster_scatter_view,
     #'CorrelogramView': controller.create_correlogram_view,
     # 'ISIView': controller._make_histogram_view(ISIView, controller._get_isi),
     # 'FiringRateView': controller._make_histogram_view(FiringRateView, controller._get_firing_rate),
    #'AmplitudeView': controller.create_amplitude_view,
    #'ProbeView': controller.create_probe_view,
    'RasterView': controller.create_raster_view,
    #'IPythonView': controller.create_ipython_view,
}


gui = GUI(
    name='TemplateGUI',
    subtitle=str('/home/guillaume/pynapple/data/A8604-211122'),
    config_dir=None,
    local_path='/home/guillaume/pynapple/data/A8604-211122/.phy/state.json',
    default_state_path='/home/guillaume/pynarchy/static/state.json',
    view_creator=view_creator,
    default_views=('WaveformView', 'CorrelogramView', 'FeatureView', 'AmplitudeView', 'TraceView', 'ProbeView', 'TemplateFeatureView'),
    enable_threading=True,
    )




###############################################
# Initial actions when creating views.

from phylib.utils import emit, connect, unconnect

@connect
def on_view_attached(view, gui_):
    print(view)
    print(gui_)
    if gui_ != gui:
        return

    # Add default color schemes in each view.
    if isinstance(view, BaseColorView):
        controller._add_default_color_schemes(view)

    if isinstance(view, ManualClusteringView):
        # Add auto update button.
        view.dock.add_button(
            name='auto_update', icon='f021', checkable=True, checked=view.auto_update,
            event='toggle_auto_update', callback=view.toggle_auto_update)

        # Show selected clusters when adding new views in the GUI.
        view.on_select(cluster_ids=controller.supervisor.selected_clusters)

# Get the state's current sort, and make sure the cluster view is initialized with it.
controller.supervisor.attach(gui)
controller.create_misc_actions(gui)
gui.set_default_actions()

gui.view_actions.separator()
# Keep the order of gui.default_views.

view_name = 'RasterView'

fn = gui.view_creator.get(view_name, None)
view = fn()


view.attach(gui)



############################################################
# Bind the `select_more` event to add clusters to the existing selection.
@connect
def on_select_more(sender, cluster_ids):
    controller.supervisor.select(controller.supervisor.selected + cluster_ids)

@connect
def on_request_select(sender, cluster_ids):
    controller.supervisor.select(cluster_ids)

# Prompt save.
@connect(sender=gui)
def on_close(sender):
    unconnect(on_view_attached, controller)
    unconnect(on_select_more, controller)
    unconnect(on_request_select, controller)
    # Show save prompt if an action was done.
    do_prompt_save = True
    if do_prompt_save and controller.supervisor.is_dirty():  # pragma: no cover
        r = _prompt_save()
        if r == 'save':
            controller.supervisor.save()
        elif r == 'cancel':
            # Prevent closing of the GUI by returning False.
            return False
        # Otherwise (r is 'close') we do nothing and close as usual.

# Status bar handler
from apps.base import StatusBarHandler

handler = StatusBarHandler(gui)
# handler.setLevel(logging.INFO)
# logging.getLogger('phy').addHandler(handler)

# Save the memcache when closing the GUI.
@connect(sender=gui)  # noqa
def on_close(sender):  # noqa

    # Gather all GUI state attributes from views that are local and thus need
    # to be saved in the data directory.
    for view in gui.views:
        local_keys = getattr(view, 'local_state_attrs', [])
        local_keys = ['%s.%s' % (view.name, key) for key in local_keys]
        gui.state.add_local_keys(local_keys)

    # Update the controller params in the GUI state.
    for param in controller._state_params:
        gui.state[param] = getattr(controller, param, None)

    # Save the memcache.
    gui.state['GUI_VERSION'] = controller.gui_version
    controller.context.save_memcache()

    # Remove the status bar handler when closing the GUI.
    #logging.getLogger('phy').removeHandler(handler)


emit('gui_ready', controller, gui)


gui.show()
run_app()
print("Yo")
gui.close()
#controller.model.close()
