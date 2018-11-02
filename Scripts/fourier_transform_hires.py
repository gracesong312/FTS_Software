import numpy as np
from astropy.io import fits
from scipy.interpolate import interp1d
from scipy.signal import detrend


#Load the data
atm_data = []
si_data = []
pos = np.linspace(-26.5,13.495,8000)
dx=.005

for i in range(200,219):
    fname = 'D:/Data/default_fname_%3d.fits'%i
    data = np.average(fits.getdata(fname),axis=(0,2))
    temp_pos = fits.getdata(fname,1)['position_data']
    if len(temp_pos)<1000:
        continue
    else:
        if fits.getheader(fname)['FILTER']=='si':
            si_data.append(detrend(data))
            print(i)
        else:
            atm_data.append(detrend(data))

si_data = np.asarray(si_data)
atm_data = np.asarray(atm_data)

#There are two dropouts in the silicon data that need to be patched
si_data[0,7740:7751] = si_data[0,7739]
si_data[4,1486:1503] = si_data[4,1485]

#Average data for transforms
si = np.average(si_data,axis=0)
si_avg = np.average(si_data,axis=0)
si_err = np.std(si_data,axis=0)
atm = np.average(atm_data,axis=0)
atm_avg = np.average(atm_data,axis=0)
atm_err = np.std(atm_data,axis=0)

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
lams = c/atm_Fs/1e9

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
lams = c/si_Fs/1e9

#Fs_prime = Fs*(1+np.diff(Fs)[0]/(2*np.max(Fs)))

#Load the simulated data
si_sim = np.loadtxt('C:/Users/Paul/Documents/FTS/si_wafer_1000um_45-2000GHz_n3.4.csv',skiprows=1,delimiter=',')

Fs_prime = atm_Fs*(1-np.diff(atm_Fs)[0]/(2*np.max(atm_Fs)))
from matplotlib import pyplot as plt
plt.plot(atm_Fs*1e3,si_psd/atm_psd)
plt.plot(si_sim[:,0]/1e9,si_sim[:,1])
plt.xlabel('Frequency [GHz]',fontsize=28)
plt.ylabel('Transmission',fontsize=28)
plt.tick_params(labelsize=22)
plt.xlim([0,1200])
plt.ylim([0,2])
plt.show()
