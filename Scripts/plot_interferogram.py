from matplotlib import pyplot as plt
import pyfits
import numpy as np

data = np.average(pyfits.getdata('C:\Users\Philip\Desktop\FTS_Software\Data\default_fname_252.fits'),axis=(0,2))
err = np.std(pyfits.getdata('C:\Users\Philip\Desktop\FTS_Software\Data\default_fname_252.fits'),axis=(0,2))
pos = pyfits.getdata('C:\Users\Philip\Desktop\FTS_Software\Data\default_fname_252.fits',1)['position_data']

plt.errorbar(pos,data,err)
plt.show()