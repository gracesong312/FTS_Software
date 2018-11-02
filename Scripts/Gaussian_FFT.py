#from scipy import signal
#from mpl_toolkits.mplot3d import Axes3D
from scipy import fftpack
from scipy.stats import norm
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import UnivariateSpline,SmoothBivariateSpline
from scipy.optimize import curve_fit




#Makes Circular Hill of Radius R and number of samples N
def disk(N,R):
    matrix = [[0 for x in range(N)] for y in range(N)]
    for i in range(N):
        for j  in range(N):
          if (i-N/2)**2 + (j-N/2)**2 < (R*N/2)**2:
            matrix[i][j] = 1
    return matrix

# Number of samplepoints
N = 1024

#Gaussian Parameters
sigma_x = 0.25
sigma_y = 0.25
y_offset = 0
x_offset= 0
width = 0.25

#X and Y coordinate arrays
x = np.linspace(4.0, 6.0, N)
y = np.linspace(4.0, 6.0, N)
x, y = np.meshgrid(x, y)

 


#Makes Gaussian given x and y coordinates and gaussian features
def makeGaussian(x,y,s_x,s_y,x_o,y_o):
    return 1/(2*np.pi*s_x*s_y) * np.exp(-((x-5-x_o)**2/(2*s_x**2)
        + (y-5-y_o)**2/(2*s_y**2)))
  

  
z = disk(N,width)*makeGaussian(x,y,sigma_x,sigma_y,x_offset,y_offset) 
#z = disk(N,0.4)



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

#plot(z,4,6,4,6)


#Calculate the Eccentricity of the fft at half max height    
def calculateEccentricity(x_o,y_o):
    z = disk(N,width)*makeGaussian(x,y,sigma_x,sigma_y,x_o,y_o) 
    f1 = fftpack.fftshift(fftpack.fft2(z))/np.sqrt(2*N)
    x1 = np.linspace(4.0, 6, N)
    y1 = np.linspace(4.0, 6, N)
    spline1 = UnivariateSpline(x1,abs(f1)[N/2-1]-np.max(abs(f1))/2,s=0)
    r1 = spline1.roots()
    radius1 = r1[len(r1)/2]-r1[len(r1)/2-1]
    spline2 = UnivariateSpline(y1,abs(f1)[:,N/2-1]-np.max(abs(f1))/2,s=0)
    r2 = spline2.roots()
    #plt.plot(x1,spline1(x1))
    #plt.plot(y1,spline2(x1))
    radius2 = r2[len(r2)/2]-r2[len(r2)/2-1]
    plt.show()
    return radius1/radius2
  
#Plot the eccentricity
def plotEccentricity(n,show=True):  
    x_array = np.linspace(0.0, 0.5, n)
    y_array = np.linspace(0.0, 0.5, n)
    for k in range(n):
        y_array[k] = calculateEccentricity(0,k/(float(n-1)*8))
        #print y_array[k]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x_array,y_array)
    ax.set_xlabel('Offset (fraction of std dev)')
    ax.set_ylabel('Minor axis/Major axis at Half Maximum')
    if show:
        plt.show()
    else:
        plt.savefig(show)

plotEccentricity(50)
#print calculateEccentricity(0,8)


