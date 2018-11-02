'''
Small script to help determine how to have two
line of communication open on the motor.
'''
import socket
import time
HOST = '192.168.1.2' #Host address
PORT = 8000 #port number for socket

positions = []
counter = 0
    
motor = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Init socket (TCP/IP)
motor.settimeout(100)
motor.connect((HOST,PORT))
motor.send('ENABLE X\n') #Send enable command
response = motor.recv(1024)
start=time.time()
motor.send('HOME X\n')
response = motor.recv(1024)
end=time.time()

def FTScode(NoOfDets,distance,stepsize,windowsize):

    Fs = 500. #replace with sampling rate
    time_step = 1/Fs

    for i in range(int(distance/stepsize)):
        motor.send('MOVEINC X0.04\n') #0.04 is the step size in mm
        d = [[0 for m in range(windowsize)] for n in range(NoOfDets)]
        d = np.asarray(d)


FTScode(1,20.0,0.04,1000)
#motor.send('WAIT MODE NOWAIT\n')
#response = motor.recv(1024)
'''
motor.send('MOVEINC X 10 XF 1\n')
response = motor.recv(1024)
while counter<(1000):
    motor.send('PFBK X\n')
    positions.append(float(motor.recv(1024).strip()[1:]))
    time.sleep(.01)
    counter+=1
'''
motor.send('DISABLE X\n') #Send enable command
response = motor.recv(1024)
motor.close()