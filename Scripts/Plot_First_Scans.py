import numpy as np
from matplotlib import pyplot as plt
from scipy.signal import detrend

#123 - LN2 hi-res with aperture
#124 - LN2 hi-res without aperture
#126 - LN2 low-res without aperture
#127 - LN2 low-res without aperture +delta 1/2 step

def load_data(fname):
    import pyfits
    data = np.squeeze(pyfits.open(fname)[0].data)
    pos = pyfits.open(fname)[1].data['position_data']
    avg = np.average(data,axis=1)
    std = np.std(data,axis=1)
    return pos, avg, std    
    

#Load the data
fname = 'D:/Data/default_fname_%3i.fits'
fnums = [123,124,126,127]
data = {}
for (i,num) in enumerate(fnums):
    pos,avg,std = load_data(fname%num)
    #Remove dropouts - remove greater than 1% variation changes
    ind = np.where(abs(np.diff(avg))/avg[:-1]>.01)[0]
    data[i] = [np.delete(vals,(ind,ind+1)) for vals in [pos,avg,std]]
    

#Plot a comparison between the aperture and full beam hi-res scans
fig,ax = plt.subplots()
ax.errorbar(data[0][0],detrend(data[0][1]),data[0][2])
ax.errorbar(data[1][0],detrend(data[1][1]),data[1][2])
ax.tick_params(labelsize=18)
ax.set_xlabel('Position [mm]',fontsize=24)
ax.set_ylabel('Signal [V]',fontsize=24)
ax.set_title('Hi-res aperture comparison',fontsize=32)
ax.legend(['w/ aperture','w/out aperture'],frameon=False,prop={'size':16})
plt.show()

#Plot a comparison between the aperture and full beam hi-res scans
fig,ax = plt.subplots()
ax.errorbar(data[0][0],data[1][1]-np.average(data[1][1]),data[0][2])
ax.errorbar(data[1][0],detrend(data[1][1]),data[1][2])
ax.tick_params(labelsize=18)
ax.set_xlabel('Position [mm]',fontsize=24)
ax.set_ylabel('Signal [V]',fontsize=24)
ax.set_title('Detrending w/ aperture',fontsize=32)
ax.legend(['Shifted','Detrended'],frameon=False,prop={'size':16})
plt.show()

#Plot comparison of two lo-res spectra

fig,ax = plt.subplots()
ax.errorbar(data[2][0],detrend(data[2][1]),data[2][2])
ax.errorbar(data[3][0],detrend(data[3][1]),data[3][2])
ax.tick_params(labelsize=18)
ax.set_xlabel('Position [mm]',fontsize=24)
ax.set_ylabel('Signal [V]',fontsize=24)
ax.set_title('Lo-res Comparisons',fontsize=32)
ax.legend(['Scan #1', 'Scan#2'],frameon=False,prop={'size':16})
plt.show()

fig,ax = plt.subplots()
ax.errorbar(data[2][0],data[2][1]-np.average(data[2][1]),data[2][2])
ax.errorbar(data[2][0],detrend(data[2][1]),data[2][2])
ax.tick_params(labelsize=18)
ax.set_xlabel('Position [mm]',fontsize=24)
ax.set_ylabel('Signal [V]',fontsize=24)
ax.set_title('Detrending w/out aperture',fontsize=32)
ax.legend(['Raw', 'Detrended'],frameon=False,prop={'size':16})
plt.show()


#Reload data without removing dropouts to allow for uniform sampling
data = {}
for (i,num) in enumerate(fnums):
    pos,avg,std = load_data(fname%num)
    data[i] = [vals for vals in [pos,avg,std]]
    
N = 500                                                  # Number of Data points
df = 1/2.5e-3                                         # Inverse of length of Canali
dt = .01e-3                                     # time-step
fN = 1./(2.*dt)                                                     # Nyquist Frequency
fvec=(np.arange(0,N)-N/2+1)*df                                      # set up frequency array
fvec_roll=np.roll(fvec,int(N/2+1))                                  # shifts frequencies for DFT ordering
xfft = np.fft.fft(data[2][1])