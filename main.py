'''
    Minimal working example

'''

import numpy as np
import matplotlib.pyplot as plt
import pynapple as nap

DATA_DIRECTORY = '/home/guillaume/pynapple/your/path/to/A2929-200711'

# LOADING DATA
data = nap.load_session(DATA_DIRECTORY, 'neurosuite')

spikes = data.spikes

#########################################################################

a = 1

tmp = locals()
pynavar = {}
for k in tmp.keys():                                                           
    if hasattr(tmp[k], '__module__'):
        if "pynapple" in a[k].__module__ and k[0] != '_':
            pynavar[k] = tmp[k]


#####################################################
