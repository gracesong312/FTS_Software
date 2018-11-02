"""This script is used to communicate between the arduino and python. ser is the 
serial port (basically the usb port) that the arduino is connected to. The only 
thing you should worry about changing there is the 'COM5', which is just whichever
port you have your arduino connected to (you can use any COM as long as it matches).
Whatever you write to the serial connection should be picked up by the arduino; the
only restriction is whatever you pass through the connection must be a char,
not a string or int. Since the move command automatically closes the connection, 
if you want to send another command through the port you will need to call ser.open().
Make sure when you are done that you close the connection, or else the file can
become corrupted. Lastly, make sure that you upload the appropriate arduino script
before you try to send anything through the serial port. Once it's uploaded, it will
remain on the arduino until you upload something else, so you should only have to 
do that part once unless you make changes.

Good luck and let me know if you have any questions!
"""



import serial
ser = serial.Serial('COM5',9600,timeout = 1)

def move(speed):
    ser.write(chr(speed))
    ser.close()
    
  