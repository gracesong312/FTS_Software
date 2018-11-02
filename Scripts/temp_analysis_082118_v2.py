# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 17:21:11 2018

@author: Philip
"""
import numpy as np
from astropy.io import fits
from scipy.interpolate import interp1d
from scipy.signal import detrend


#Create the position vector
si_num,atm_num=329,325
pos = np.linspace(-26.5,13.5,1600)
dx = .025


############################# Silicon ##########################################

#Load the silizon data
fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_%3d.fits'%si_num
si_sens = fits.getheader(fname)['LI-SENSITIVITY']
si_avg = np.average(fits.getdata(fname),axis=(0,2))*si_sens#Polynomial removal 
p = np.polyfit(pos,si_avg,3)
fit = np.polyval(p,pos)
si = si_avg-fit
si_err = np.std(fits.getdata(fname),axis=(0,2))

#Roll the interferogram
si_ind = np.argmax(np.abs(si))
si_nsteps = np.min((si_ind,len(si)-si_ind))
si = np.roll(si[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)
si_pos = np.roll(pos[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)

#Perform the fft
si_fft = np.fft.fft(si)
si_phi = np.angle(si_fft)
si_amplitude = np.abs(si_fft)**2
si_fft_corr = si_fft.real*np.cos(si_phi)+si_fft.imag*np.sin(si_phi)
si_psd = np.abs(si_fft_corr[:len(si_fft)/2])**2 #psd = power spectral density

#The trickiest part - creating the x-axis
c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
si_Fs = F_max/2*np.linspace(0,1,len(si_fft)/2)


############################# Atmosphere #######################################


#Load the atmosphere data
fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_%3d.fits'%atm_num
atm_sens = fits.getheader(fname)['LI-SENSITIVITY']
atm_avg = np.average(fits.getdata(fname),axis=(0,2))*atm_sens
p = np.polyfit(pos,atm_avg,3)
fit = np.polyval(p,pos)
atm = atm_avg - fit
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

#The trickiest part - creating the x-axis
c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
atm_Fs = F_max/2*np.linspace(0,1,len(atm_fft)/2)

trans1 = si_psd/atm_psd

#Create the position vector
si_num,atm_num=331,325
pos = np.linspace(-26.5,13.5,1600)
dx = .025


############################# Silicon ##########################################

#Load the silizon data
fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_%3d.fits'%si_num
si_sens = fits.getheader(fname)['LI-SENSITIVITY']
si_avg = np.average(fits.getdata(fname),axis=(0,2))*si_sens#Polynomial removal 
p = np.polyfit(pos,si_avg,3)
fit = np.polyval(p,pos)
si = si_avg-fit
si_err = np.std(fits.getdata(fname),axis=(0,2))
#Roll the interferogram
si_ind = np.argmax(np.abs(si))
si_nsteps = np.min((si_ind,len(si)-si_ind))
si = np.roll(si[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)
si_pos = np.roll(pos[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)

#Perform the fft
si_fft = np.fft.fft(si)
si_phi = np.angle(si_fft)
si_amplitude = np.abs(si_fft)**2
si_fft_corr = si_fft.real*np.cos(si_phi)+si_fft.imag*np.sin(si_phi)
si_psd = np.abs(si_fft_corr[:len(si_fft)/2])**2 #psd = power spectral density

#The trickiest part - creating the x-axis
c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
si_Fs = F_max/2*np.linspace(0,1,len(si_fft)/2)


############################# Atmosphere #######################################

#Load the atmosphere data
fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_%3d.fits'%atm_num
atm_sens = fits.getheader(fname)['LI-SENSITIVITY']
atm_avg = np.average(fits.getdata(fname),axis=(0,2))*atm_sens
p = np.polyfit(pos,atm_avg,3)
fit = np.polyval(p,pos)
atm = atm_avg - fit
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

#The trickiest part - creating the x-axis
c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
atm_Fs = F_max/2*np.linspace(0,1,len(atm_fft)/2)

trans2 = si_psd/atm_psd

#Create the position vector
si_num,atm_num=333,325
pos = np.linspace(-26.5,13.5,1600)
dx = .025


############################# Silicon ##########################################

#Load the silizon data
fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_%3d.fits'%si_num
si_sens = fits.getheader(fname)['LI-SENSITIVITY']
si_avg = np.average(fits.getdata(fname),axis=(0,2))*si_sens#Polynomial removal 
p = np.polyfit(pos,si_avg,3)
fit = np.polyval(p,pos)
si = si_avg-fit
si_err = np.std(fits.getdata(fname),axis=(0,2))
#Roll the interferogram
si_ind = np.argmax(np.abs(si))
si_nsteps = np.min((si_ind,len(si)-si_ind))
si = np.roll(si[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)
si_pos = np.roll(pos[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)

#Perform the fft
si_fft = np.fft.fft(si)
si_phi = np.angle(si_fft)
si_amplitude = np.abs(si_fft)**2
si_fft_corr = si_fft.real*np.cos(si_phi)+si_fft.imag*np.sin(si_phi)
si_psd = np.abs(si_fft_corr[:len(si_fft)/2])**2 #psd = power spectral density

#The trickiest part - creating the x-axis
c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
si_Fs = F_max/2*np.linspace(0,1,len(si_fft)/2)


############################# Atmosphere #######################################

#Load the atmosphere data
fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_%3d.fits'%atm_num
atm_sens = fits.getheader(fname)['LI-SENSITIVITY']
atm_avg = np.average(fits.getdata(fname),axis=(0,2))*atm_sens
p = np.polyfit(pos,atm_avg,3)
fit = np.polyval(p,pos)
atm = atm_avg - fit
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

#The trickiest part - creating the x-axis
c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
atm_Fs = F_max/2*np.linspace(0,1,len(atm_fft)/2)

trans3 = si_psd/atm_psd

#Create the position vector
si_num,atm_num=334,325
pos = np.linspace(-26.5,13.5,1600)
dx = .025


############################# Silicon ##########################################

#Load the silizon data
fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_%3d.fits'%si_num
si_sens = fits.getheader(fname)['LI-SENSITIVITY']
si_avg = np.average(fits.getdata(fname),axis=(0,2))*si_sens#Polynomial removal 
p = np.polyfit(pos,si_avg,3)
fit = np.polyval(p,pos)
si = si_avg-fit
si_err = np.std(fits.getdata(fname),axis=(0,2))
#Roll the interferogram
si_ind = np.argmax(np.abs(si))
si_nsteps = np.min((si_ind,len(si)-si_ind))
si = np.roll(si[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)
si_pos = np.roll(pos[si_ind-si_nsteps:si_ind+si_nsteps],si_nsteps)

#Perform the fft
si_fft = np.fft.fft(si)
si_phi = np.angle(si_fft)
si_amplitude = np.abs(si_fft)**2
si_fft_corr = si_fft.real*np.cos(si_phi)+si_fft.imag*np.sin(si_phi)
si_psd = np.abs(si_fft_corr[:len(si_fft)/2])**2 #psd = power spectral density

#The trickiest part - creating the x-axis
c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
si_Fs = F_max/2*np.linspace(0,1,len(si_fft)/2)


############################# Atmosphere #######################################

#Load the atmosphere data
fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_%3d.fits'%atm_num
atm_sens = fits.getheader(fname)['LI-SENSITIVITY']
atm_avg = np.average(fits.getdata(fname),axis=(0,2))*atm_sens
p = np.polyfit(pos,atm_avg,3)
fit = np.polyval(p,pos)
atm = atm_avg - fit
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

#The trickiest part - creating the x-axis
c = 2.99792458e11 #[mm/s]
F_max = c/(4*dx*np.cos(12.2*np.pi/180)*np.cos(5.78/2.*np.pi/180)*1e12) #[THz]
atm_Fs = F_max/2*np.linspace(0,1,len(atm_fft)/2)

trans4 = si_psd/atm_psd


'''
There can be a small correction factor applied to the frequencies, if it helps.
This is usually less than a 1\% shift however.
'''
#Fs_prime = Fs*(1+np.diff(Fs)[0]/(2*np.max(Fs)))



trans = np.average([trans1,trans2,trans3,trans4],axis=0)
trans_err = np.std([trans1,trans2,trans3,trans4],axis=0)


#Load Goddard data

from matplotlib import pyplot as plt
#plt.plot(atm_Fs*1e3,trans1,alpha=.5)
#plt.plot(atm_Fs*1e3,trans2,alpha=.5)
#plt.plot(atm_Fs*1e3,trans3,alpha=.5)
#plt.plot(atm_Fs*1e3,trans4,alpha=.5)
plt.plot(atm_Fs*1e3,trans,alpha=.5)
plt.plot(atm_Fs*1e3,atm_psd/1000000)
plt.xlabel('Frequency [GHz]',fontsize=28)
plt.ylabel('Transmission',fontsize=28)
plt.tick_params(labelsize=22)
plt.xlim([0,1200])
plt.ylim([0,2])
plt.show()

