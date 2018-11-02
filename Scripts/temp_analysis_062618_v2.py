'''
This script looks at making an FFT for each sample in the time stream and 
averaging the 40 samples together at the end - it gives comparable signal to
those that are averaged first at then taking the FFT.
'''

import numpy as np
from astropy.io import fits
from scipy.interpolate import interp1d
from scipy.signal import detrend

#Create the position vector
scale_atm=1
si_num,atm_num=303,304
pos = np.linspace(-26.5,13.495,1600)
dx = .025


############################# Silicon ##########################################

#Load the silizon data
fname = 'D:/Data/default_fname_%3d.fits'%si_num
si_data = np.squeeze(fits.getdata(fname))
fname = 'D:/Data/default_fname_%3d.fits'%atm_num
atm_data = np.squeeze(fits.getdata(fname))

c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
Fs = F_max/2*np.linspace(0,1,1598/2)

trans = []

for i in range(40):
    si = detrend(si_data[:,i])

    si_ind = np.argmax(np.abs(si))
    si_nsteps = np.min((si_ind,len(si)-si_ind))
    si = np.roll(si[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)
    si_pos = np.roll(pos[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)

    si_fft = np.fft.fft(si)
    si_phi = np.angle(si_fft)
    si_amplitude = np.abs(si_fft)**2
    si_fft_corr = si_fft.real*np.cos(si_phi)+si_fft.imag*np.sin(si_phi)
    si_psd = np.abs(si_fft_corr[:len(si_fft)/2])**2 

    #Load the atmosphere data

    atm = detrend(np.average(fits.getdata(fname),axis=(0,2)))*scale_atm
    atm_avg = np.average(fits.getdata(fname),axis=(0,2))
    atm_err = np.std(fits.getdata(fname),axis=(0,2))
    
    #Roll the interferogram
    atm_ind = np.argmax(np.abs(atm))
    atm_nsteps = np.min((atm_ind,len(atm)-atm_ind))
    atm = np.roll(atm[atm_ind-atm_nsteps:atm_ind+atm_nsteps],atm_nsteps)
    atm_pos = np.roll(pos[atm_ind-atm_nsteps:atm_ind+atm_nsteps],atm_nsteps)
    
    #Perform the fft
    atm_fft = np.fft.fft(atm)
    atm_phi = np.angle(atm_fft)
    atm_amplitude = np.abs(atm_fft)**2
    atm_fft_corr = atm_fft.real*np.cos(atm_phi)+atm_fft.imag*np.sin(atm_phi)
    atm_psd = np.abs(atm_fft_corr[:len(atm_fft)/2])**2 #psd = power spectral density
    
    trans.append(si_psd/atm_psd)


from matplotlib import pyplot as plt
from scipy.signal import medfilt
plt.errorbar(Fs*1e3,np.average(trans,axis=0),np.std(trans,axis=0))
plt.xlabel('Frequency [GHz]',fontsize=28)
plt.ylabel('Transmission',fontsize=28)
plt.tick_params(labelsize=22)
plt.xlim([0,1200])
plt.ylim([0,5])
plt.show()
