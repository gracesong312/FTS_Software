# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 12:36:43 2018

@author: Philip
"""

from matplotlib import pyplot as plt
from astropy.io import fits
import numpy as np

fname = 'C:\Users\Philip\Desktop\FTS_Software\Data\default_fname_195.fits'
data = np.average(fits.getdata(fname),axis=(0,2))
pos = fits.getdata(fname,1)['position_data']

plt.plot(pos,data)
plt.show()