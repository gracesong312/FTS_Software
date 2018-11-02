'''
Script to plot the convolved transmission of the FTS windows
'''

import numpy as np
from scipy.optimize import leastsq
from scipy.interpolate import interp1d

#Load the data
c = 2.99792458e11 #[mm/s]
fluorogold = np.loadtxt('C:/Users/Paul/Desktop/windows/Flourogold_Transmission.csv',delimiter=',')
teflon = np.loadtxt('C:/Users/Paul/Desktop/windows/Teflon_Transmission.csv',delimiter=',')
water_F = []
water_T = []
lines = open('C:/Users/Paul/Desktop/windows/water.5mm.txt').readlines()
for line in lines:
    vals = line.split()
    water_F.append(float(vals[0]))
    if 'E' not in vals[2]:
        water_T.append(0)
    else:
        water_T.append(float(vals[2]))
water_F = np.asarray(water_F)
water_T = np.asarray(water_T)
water_lams = c/water_F/1e6

#Fit a power law to the flurogold absorption coefficient
# A = -1/t*log(T), t= sample thickness, T = transmission
#Power law observed in literature and in our data
# A = a*nu**b
#Halpern et al. 1986 https://doi.org/10.1364/AO.25.000565

# log(A) = log(a)+b*log(nu)
logx = np.log10(10000./fluorogold[:,0]) #Frequency [cm^-1]
logA = np.log10(-1/.16*np.log(fluorogold[:,1])) #Absorption coefficient [cm^-1]
p = np.polyfit(logx,logA,1)

#Now let's fit our transmission over the wavelengths of interest
@np.vectorize
def calc_T(lam,include_water=True):
    
    #Use a flat transmisison for wavelengths >160um
    teflon_interp = interp1d(teflon[:,0],teflon[:,1],bounds_error=False,fill_value=.7)
    
    #Use the measured transmission where defined, otherwise the power law
    if ((np.min(fluorogold[:,0])<lam)&(lam<np.max(fluorogold[:,0]))):
        fluorogold_interp = interp1d(fluorogold[:,0],fluorogold[:,1])
    else:
        nu = np.linspace(1e4/20,1e4/1.5e6,1e4)
        logA = np.polyval(p,np.log10(nu))
        T = np.exp(-.16*10**logA)
        fluorogold_interp = interp1d(1e4/nu,T,bounds_error=False,fill_value=0)
        
    if include_water:
        water_interp = interp1d(water_lams,water_T)
        return teflon_interp(lam)*fluorogold_interp(lam)*water_interp(lam)        
    else:
        return teflon_interp(lam)*fluorogold_interp(lam)
        
    
wave = np.linspace(150,1500,1e3)
#wave = c/Fs/1e9
wave = c/Fs_prime[50:800]/1e9
T1 = calc_T(wave,False)
T2 = calc_T(wave,True)

#Can use these lines to match the spectrometer resolution
#wave = c/Fs[8:38]/1e9
#wave = c/Fs_prime[8:38]/1e9
#Fs_prime would account for the small shift in wavenumber from the dispersion