'''
    Minimal working example

'''
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pynapple as nap
from pynaception import scope


DATA_DIRECTORY = '/mnt/home/gviejo/pynapple/your/path/to/MyProject/sub-A2929/A2929-200711'

# LOADING DATA
data = nap.load_session(DATA_DIRECTORY, 'neurosuite')
spikes = data.spikes
position = data.position
angle = position['ry']
wake_ep = data.epochs['wake']

lfp = data.load_lfp(channel=15)


scope(globals())

