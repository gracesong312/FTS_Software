# -*- coding: utf-8 -*-
import socket
import sys
from time import sleep
#from LabJackPython import ljm
import numpy as np
import array
import os

## Init  Labjack T7---------------------------------------------

#handle = ljm.open(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")
#address = 1000 # DAC0 port number
#dataType = ljm.constants.FLOAT32 

## Define some constants
HOST = '192.168.1.2' #Host address
PORT = 8001 #port number for socket
    
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Init socket (TCP/IP)
s.connect((HOST,PORT)) #Bind HOST,PORT to socket
s.send('ENABLE X\n') #Send enable command
data = s.recv(1024) #Collect and print response
print 'received: ', repr(data)

## Start stage control loop---------------------------------------
#s.send('MOVEABS X64.87 F20\n')
sleep(1)
s.send('MOVEABS X-50.87 F20\n')#move to starting point
sleep(1)
s.send('HOME X\n') #Send home command
s.send('PFBK(X)\n')
pos = s.recv(1024)
s.send('DISABLE X\n')
print 'received: ', repr(data)
 

## Data acquisition-————————————————————————

def FTScode(NoOfDets,distance,stepsize,windowsize):

    Fs = 500. #replace with sampling rate
    time_step = 1/Fs

    for i in range(int(distance/stepsize)):
        s.send('MOVEINC X0.04\n') #0.04 is the step size in mm
        d = [[0 for m in range(windowsize)] for n in range(NoOfDets)]
        d = np.asarray(d)

    #s.close() #Close serial connection


FTScode(1,20.0,0.04,1000)
s.close()