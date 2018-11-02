from scipy import fftpack
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import UnivariateSpline
from scipy.optimize import curve_fit
import plotly.plotly as py
import plotly.figure_factory as ff

#Makes Circular Hill of Radius R and number of samples N
def disk(N,R):
    matrix = [[0 for x in range(N)] for y in range(N)]
    radius = (R*N/(stop-start))**2
    for i in range(N):
        for j  in range(N):
          if (i-N/2)**2 + (j-N/2)**2 < radius:
            matrix[i][j] = 1
    return matrix

#Optics Tubes Parameters
F = 3.0
wavelength = 0.2
D_scale = 2.31
D = D_scale*F*wavelength
omega_o = D / 3.2
Z = 36.19
sigma = Z*wavelength/(2.*np.pi*omega_o)
scaling_factor = 1.0


#py.sign_in('plj32','TJM5t4xuZR2C8uHoapbh')


def calculateSigma(D_scale):
        D = D_scale*F*wavelength
        omega_o = D/3.2
        sigma = Z*wavelength/(2.*np.pi*omega_o)
        return sigma

cell_text = [['F_lambda (f3 at 2mm)','Beam Size'], 
[0.67, calculateSigma(0.67)], 
[0.77,calculateSigma(0.77)] ,
[0.82,calculateSigma(0.82)], 
[1.49,calculateSigma(1.49)],
[2.31, calculateSigma(2.31)],
[4.14,calculateSigma(4.14)]]

#table = ff.create_table(cell_text)
#py.iplot(table,filename = "Gaussian_size1")


def apEff(D):
    wf = 3.2
    w0 = D/wf
    return 1. - np.exp(-((np.pi**2)/2.)*(w0**2))
    
def ET(eff):
    return 10.*np.log10(1. - eff)
    
taper = ET(apEff(D/(F*wavelength)))


# Number of samplepoints
N = 2048

#Gaussian Parameters
sigma_x = sigma/scaling_factor
sigma_y = sigma/scaling_factor
y_offset = 5
x_offset= 0
#width = 2*13.41/scaling_factor
width = Z/F
start = -5.0
stop = 15.0

#X and Y coordinate arrays
x = np.linspace(start, stop, N)
y = np.linspace(start, stop, N)
x, y = np.meshgrid(x, y)

 


#Makes Gaussian given x and y coordinates and gaussian features
def makeGaussian(x,y,s_x,s_y,x_o,y_o):
    return 1/(2*np.pi*s_x*s_y) * np.exp(-((x-5-x_o)**2/(2*s_x**2)
        + (y-5-y_o)**2/(2*s_y**2)))
  
def gaussian(x,s):
    return 1/(2*np.pi*s) * np.exp(-((x)**2/(2*s**2)))
    
def gaus(x,a,sigma):
    return a*np.exp(-(x-5)**2/(2*sigma**2))
  
z = disk(N,width/2)*makeGaussian(x,y,sigma_x,sigma_y,x_offset,y_offset) 
#z = disk(N,0.4)


def plotGaussians():
    xg = np.linspace(-30.0, 30.0, N)
    for k in range(9):
        F = 1.37
        wavelength = 0.3
        D_scale = 0.5+k*0.25
        D = D_scale*F*wavelength
        omega_o = D / 3.2
        z = 36.19
        sigma = z*wavelength/(2.*np.pi*omega_o)
        c = gaussian(xg,sigma)
        plt.plot(xg,c,label = '%.2f F lambda, taper = %.2f'%(D_scale,ET(apEff(D_scale))))
        plt.legend()

    plt.show()

#plotGaussians()

#Plots the graphs
def plot(z,xmin,xmax,ymin,ymax,show = True):
    plt.figure(1)
    plt.contourf(x, y, z,)
    axes1 = plt.gca()
    axes1.set_xlim([xmin,xmax])
    axes1.set_ylim([ymin,ymax])
    plt.colorbar()
    plt.figure(2) 
    f1 = fftpack.fftshift(fftpack.fft2(z))
    plt.contourf(x,y,np.log(abs(f1)))
    axes2 = plt.gca()
    axes2.set_xlim([xmin,xmax])
    axes2.set_ylim([ymin,ymax])
    plt.colorbar()
    if show:
        plt.show()
    else:
        plt.savefig(show)

#plot(z,start,stop,start,stop)


#Calculate the Eccentricity of the fft at half max height    
def calculateEccentricity(x_o,y_o,sigma_x,sigma_y):
    z = disk(N,width)*makeGaussian(x,y,sigma_x,sigma_y,x_o,y_o) 
    f1 = fftpack.fftshift(fftpack.fft2(z))
    x1 = np.linspace(start, stop, N)
    y1 = np.linspace(start, stop, N)
    poptx,pcov = curve_fit(gaus,x1,(abs(f1))[N/2])
    popty,pcov = curve_fit(gaus,y1,(abs(f1))[:,N/2])
    #spline1 = UnivariateSpline(x1,(abs(f1))[N/2-1]-(np.max((abs(f1))[N/2-1]))/2,s=0)
    #r1 = spline1.roots()
    #radius1 = r1[len(r1)/2]-r1[len(r1)/2-1]
    #xw = np.linspace(5-radius1/2.0,radius1/2.0 + 5, 20)
    #yw = np.zeros(20)
    #plt.plot(xw,yw)
    #spline2 = UnivariateSpline(y1,(abs(f1))[:,N/2-1]-(np.max((abs(f1))[:,N/2-1]))/2,s=0)
    #r2 = spline2.roots()
    #plt.plot(x1,spline1(x1))
    #plt.plot(y1,spline2(x1))
    #radius2 = r2[len(r2)/2]-r2[len(r2)/2-1]
    return abs(2*np.sqrt(2*np.log(2))*popty[1]/(2*np.sqrt(2*np.log(2))*poptx[1]))#,radius1,radius2
    

fig = plt.figure()
ax = fig.add_subplot(111)
#Plot the eccentricity
def plotEccentricity(n,scale,show=True):  
    #x_array = np.zeros(n)
    x_array = np.linspace(0.0,0.5,n)
    y_array = np.zeros(n)
    sigma_x = calculateSigma(scale)
    sigma_y = sigma_x
    divisor = float(n-1)*1.0/sigma_x*2
    #divisor = float(n-1)*0.5/width*2
    #theta = np.arctan(F*2)*180/np.pi
    for k in range(n):
        #theta_prime = np.arctan(k/divisor/Z*2)*180/np.pi
        #x_array[k] = theta_prime/theta
        y_array[k] = calculateEccentricity(0,k/divisor,sigma_x,sigma_y)
        #print y_array[k]
    ax.plot(x_array,y_array,label = '%.1ff lambda'%scale)
    ax.set_xlabel('Offset (fraction of stop)')
    ax.set_ylabel('Minor axis/Major axis at Half Maximum')
    #ax.set_title('%.2f F Lambda taper = %.1f dB' %(D_scale,taper))
    ax.set_title('f%.1f at %dmm' %(F,wavelength*10))
    if show:
        plt.legend(loc = 0)
        pass
    else:
        plt.savefig(show)


plotEccentricity(5,.41/(F*wavelength))
plotEccentricity(5,.47/(F*wavelength))
plotEccentricity(5,.6/(F*wavelength))
plotEccentricity(5,.9/(F*wavelength))
plotEccentricity(5,1.47/(F*wavelength))
plotEccentricity(5,2.5/(F*wavelength))
plt.show()
#print calculateEccentricity(0,sigma/scaling_factor/2.0)
