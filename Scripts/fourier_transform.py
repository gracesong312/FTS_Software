import numpy as np
from astropy.io import fits
from scipy.interpolate import interp1d
from scipy.signal import detrend

#Sampling constants
#Should be pulled from the header later
dx = .005 #[mm]

#Load the data
fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_196.fits' #173, 185
data = np.average(fits.getdata(fname),axis=(0,2))
err = np.std(fits.getdata(fname),axis=(0,2))
pos = fits.getdata(fname,1)['position_data']

#ind = np.where(((pos>=-14.5)&(pos<=.5)))
#data = data[ind]
#pos = pos[ind]

#Detrend the data with a 5th order polynomial
p = np.polyfit(pos,data,25)
fit = np.polyval(p,pos)
data-=fit

ind = np.argmax(np.abs(data))
nsteps = np.min((ind,len(data)-ind))
data = np.roll(data[ind-nsteps:ind+nsteps],nsteps)
pos = np.roll(pos[ind-nsteps:ind+nsteps],nsteps)


#Perform the fft
fft = np.fft.fft(data)
phi = np.angle(fft)
amplitude = np.abs(fft)**2
fft_corr = fft.real*np.cos(phi)+fft.imag*np.sin(phi)
psd = np.abs(fft_corr[:len(fft)/2])**2 #psd = power spectral density

#The trickiest part - creating the x-axis
c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
Fs = F_max/2*np.linspace(0,1,len(fft)/2)
lams = c/Fs/1e9


Fs_prime = Fs*(1+np.diff(Fs)[0]/(2*np.max(Fs)))

from matplotlib import pyplot as plt
plt.plot(Fs,psd)
plt.show()