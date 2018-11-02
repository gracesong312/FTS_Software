import sys, os
import random
import numpy as np
import pyfits
import pandas as pd
from copy import deepcopy as dc
from scipy.signal import medfilt2d
from viridis import viridis
import matplotlib.path as mplPath
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT# as NavigationToolbar
from matplotlib.figure import Figure
import warnings
import ast
import pickle
from thorFW102cDriver import FilterWheelDriver
from DAQCode import MultiChannelAnalogInput
import socket
from time import sleep
import array
warnings.filterwarnings("ignore")

class NavigationToolbar(NavigationToolbar2QT):
    
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home','Pan', 'Zoom', 'Save')]

    def __init__(self, *args, **kwargs):
        super(NavigationToolbar, self).__init__(*args, **kwargs)
        self.layout().takeAt(4)             
 
class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    #Took this class from example code; essentially creates the plot that displays the DAQ readout

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi) 
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)
        self.axes.set_xlabel('Time (seconds)')
        self.axes.set_ylabel('Volts')
        self.axes.set_title("DAQ Readout")
        self.compute_initial_figure()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
    def compute_initial_figure(self):
        pass       


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        timer = QTimer(self) #Creates a timer to reset the plot every 100 milliseconds
        timer.timeout.connect(self.update_figure)
        timer.start(100)

    def compute_initial_figure(self):
        pass

    def update_figure(self):
        display = MultiChannelAnalogInput(50000,5000,["Dev1/ai0"]) #Creates the channel to read from
        display.configure() #Connects to DAQ
        data = display.read() #Reads data from DAQ
        timeCoord = np.linspace(0,0.1,5000) #Creates time coordinates for plot
        self.axes.plot(timeCoord,data) #plots Data
        self.axes.set_xlabel('Time (seconds)')
        self.axes.set_ylabel('Volts')
        self.axes.set_title("DAQ Readout")
        self.draw()

class Window(QMainWindow):
    
    def __init__(self):
        super(Window,self).__init__()
        self.counter = 0
        self.HOST = '192.168.1.2'
        self.PORT = 8000
        self.setGeometry(0,30,1600,800)
        self.setWindowTitle('FTS Controller')
        self.setWindowIcon(QIcon('C:\Users\Philip\Downloads\FTS_Software\FTS_Software\\logo.png'))
        self.create_menu()
        self.init()
        
    def init(self):
        self.create_main_frame()
        self.createTextField()
        self.daqControls()
        self.createDaqWindow()
        self.motorControls()
        self.show()  
             
        
    def create_menu(self):
        #Setting up various menu controls
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        
        quit_action = self.create_action('&Quit', slot=self.close, 
            shortcut='Ctrl+Q', tip='Close the application')
            
        save_action = self.create_action('&Save As', slot=self.save,
            shortcut='Ctrl+S',tip='Save the current output')
                
        self.add_actions(fileMenu,(quit_action,save_action,))
        
        helpMenu = mainMenu.addMenu('&Help')
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About FTS Controller')
        daq_action = self.create_action("&DAQ Help",
            shortcut = 'F2', slot = self.on_daq,
            tip = 'How to use DAQ')
        fw_action = self.create_action("&Filter Wheel Help",
            shortcut = 'F3', slot = self.on_fw,
            tip = 'How to use Filter Wheel')
        motor_action = self.create_action("&Motor Help",
            shortcut = 'F4', slot = self.on_motor,
            tip = 'How to use Motor')
        self.add_actions(helpMenu, (about_action,daq_action,fw_action,motor_action))
        
        
    def save(self):
        fname = QFileDialog.getSaveFileName(self,'Select Save File')
        f = open(fname,'w')
        f.close()
        
    def motorControls(self):
        #Creating the various widgets to control the motor
        self.homeButton = QPushButton("&Home",self)#Homes the motor
        self.connect(self.homeButton,SIGNAL('clicked()'),self.homeButtonControl)
        self.homeButton.move(1000,100)
        self.enableButton = QPushButton("Enable",self)#Enables the axis
        self.connect(self.enableButton,SIGNAL('clicked()'),self.enableAxis)
        self.enableButton.move(1000,350)
        self.disableButton = QPushButton("Disable",self)#Disables the axis
        self.connect(self.disableButton,SIGNAL('clicked()'),self.disableAxis)
        self.disableButton.move(1000,400)
        self.oscillateButton = QPushButton("Oscillate",self)#Oscillates motor
        self.connect(self.oscillateButton,SIGNAL('clicked()'),self.oscillate)
        self.oscillateButton.move(1125,350)
        self.motortextbox = QLineEdit(self)#Choose how far you want motor to move
        self.motortextbox.setMinimumWidth(1)
        self.motortextbox.move(1000,200)
        self.velocitytextbox = QLineEdit(self)#Set motor speed
        self.velocitytextbox.setMinimumWidth(1)
        self.velocitytextbox.move(1000,250)
        self.amplitudetextbox = QLineEdit(self)#Choose amplitude of oscillation
        self.amplitudetextbox.setMinimumWidth(1)
        self.amplitudetextbox.move(1125,200)
        self.frequencytextbox = QLineEdit(self)#Choose frequency of oscillation
        self.frequencytextbox.setMinimumWidth(1)
        self.frequencytextbox.move(1125,250)
        self.cyclestextbox = QLineEdit(self)#Choose number of oscillation cycles
        self.cyclestextbox.setMinimumWidth(1)
        self.cyclestextbox.move(1125,300)
        self.motor_distance_label = QLabel(self)
        self.motor_distance_label.setText("Motor Position")
        self.motor_distance_label.move(1000,175)
        self.motor_velocity_label = QLabel(self)
        self.motor_velocity_label.setText("Motor Velocity")
        self.motor_velocity_label.move(1000,225)
        self.motor_amplitude_label = QLabel(self)
        self.motor_amplitude_label.setText("Oscillation Amplitude")
        self.motor_amplitude_label.move(1125,175)
        self.motor_frequency_label = QLabel(self)
        self.motor_frequency_label.setText("Oscillation Frequency")
        self.motor_frequency_label.move(1125,225)
        self.motor_cycles_label = QLabel(self)
        self.motor_cycles_label.setText("Oscillation Cycles")
        self.motor_cycles_label.move(1125,275)
        self.moveButton = QPushButton("&Move",self)#Moves the motor to specified position at specified speed
        self.connect(self.moveButton,SIGNAL('clicked()'),self.motorMovement)
        #self.connect(self.moveButton,SIGNAL('clicked()'),self.motorPos)
        self.moveButton.move(1000,300)
        
    def homeButtonControl(self):
        #Homes the motor stage
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST,self.PORT))
        self.s.send('HOME X\n')
        self.s.close()
    
    def motorMovement(self):
        #Moves the motor to position that has been specified
        self.g = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#Creates socket 
        self.g.connect((self.HOST,self.PORT))#Connects socket to motor
        self.g.send('MOVEABS X%s F%s\n'%(self.motortextbox.text(),self.velocitytextbox.text()))#Sends commands to motor
        self.g.close()#Closes the socket
    
    def enableAxis(self):
        #Enables the motor axis
        self.e = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.e.connect((self.HOST,self.PORT))
        self.e.send('ENABLE X\n')
        self.e.close()
   
    def disableAxis(self):
        #Disables the motor axis
        self.d = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.d.connect((self.HOST,self.PORT))
        self.d.send('DISABLE X\n')
        self.d.close()
    
    def oscillate(self):
        #Causes the motor to oscillate at specified frequency and amplitude
        self.o = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.o.connect((self.HOST,self.PORT))
        self.o.send('OSCILLATE X, %s, %s, %s\n'%(self.amplitudetextbox.text(),self.frequencytextbox.text(),self.cyclestextbox.text()))
        self.p.close()
    
    def motorPos(self):
        self.a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.a.connect((self.HOST,self.PORT))
        self.a.send('DATAACQ X TRIGGER 1 \n DATAACQ X INPUT 1 \n DATAACQ X ON 200')
        self.a.close()   
        
    def daqControls(self):
        #This function initializes all of the text buttoms and boxes relating to DAQ
        self.filetextbox = QLineEdit(self) #Name of file you want to write to
        self.filetextbox.setMinimumWidth(1)
        self.filetextbox.move(100,250)
        self.ratetextbox = QLineEdit(self) #Sampling rate
        self.ratetextbox.setMinimumWidth(1)
        self.ratetextbox.move(100,300)
        self.timetextbox = QLineEdit(self) #How long you sample for
        self.timetextbox.setMinimumWidth(1)
        self.timetextbox.move(100,350)
        self.channeltextbox = QLineEdit(self) #Channel you are collecting from
        self.channeltextbox.setMinimumWidth(1)
        self.channeltextbox.move(100,400)
        self.run_button = QPushButton("&Run",self) #Start collecting data
        self.connect(self.run_button, SIGNAL('clicked()'), self.runDaq)
        self.run_button.move(100,450)
        #Labels for the various buttons and text boxs       
        self.file_label = QLabel(self)
        self.file_label.setText("File Name")
        self.file_label.move(100,225)
        self.sample_label = QLabel(self)
        self.sample_label.setText("Sampling Rate")
        self.sample_label.move(100,275)
        self.time_label = QLabel(self)
        self.time_label.setText("Collection Time")
        self.time_label.move(100,325)
        self.channel_label = QLabel(self)
        self.channel_label.setText("Channel Number")
        self.channel_label.move(100,375)
        
    def runDaq(self):
        #Collects DAQ Data and saves it to a file when running
        rate = int(self.ratetextbox.text()) #Data collection rate (samples/second)
        time = float(self.timetextbox.text()) #How long you want to collect (seconds)
        samples = int(time*rate) #Samples calculated from above
        channel = ["Dev1/ai%s"%self.channeltextbox.text()] #Channel you want to collect data from
        filename = str(self.filetextbox.text()) #Name of the file you want to write to
        if samples <= 500000: #DAQ code cannot process more than 500000 samples at once
            test = MultiChannelAnalogInput(rate,samples,channel)
            iterations = 1
            timelist = np.linspace(0,time,samples)
        else: #If more than 500000 samples required, python will split the sampling into several iterations
            iterations = int(samples/500000)
            test = MultiChannelAnalogInput(rate,500000,channel)
            timelist = np.linspace(0,int(iterations*500000/rate),iterations*500000)#Creates a list of time data
        readout = []
        for k in range(iterations):
            test.configure()
            readout.append(test.read().tolist()) #Sends data to a list
        np.savetxt(filename + '.FITS',readout) #Saves data to a file specified in the box
        
    def createDaqWindow(self):
        dc = MyDynamicMplCanvas(self, width=5, height=5, dpi=100) #Creates the plot figure
        dc.move(300,100)
                
    def createTextField(self):
        #Creates text field to input filter wheel controls
        self.fwtextbox = QLineEdit(self)
        self.fwtextbox.setMinimumWidth(1)
        self.fwtextbox.move(100,100)
        self.connect(self.fwtextbox, SIGNAL('editingFinished ()'), self.filterWheelControl)
        self.fw_label = QLabel(self)
        self.fw_label.setText("Filter Wheel Position")
        self.fw_label.move(100,75)
                
    def filterWheelControl(self):
        #Used to move filter wheel
        self.f = FilterWheelDriver(p=3) #Initializes the filter wheel
        self.f.setPos(self.fwtextbox.text()) #Sets filterwheel position
        self.f.close() #Closes the device when finished
        
        
    def add_actions(self,target,actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)
    
    def create_action(self,text,slot=None,shortcut=None,
                      icon=None,tip=None,checkable=False,
                      signal='triggered()'):                      
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
        
    def on_about(self):
        msg = "This software is designed to communicate with the FTS system, specifically "\
        "with the NI USB-6002 DAQ, FW102C Thor Labs filter wheel, IR Labs bolometer, "\
        "CES100-04 blackbody, & Aerotech ANT-160-L linear motor.  Additional "\
        "components can easily be added, with the appropriate drivers.\n\n"\
        "The save menu currently outputs a FITS file containing all the parameters "\
        "stored in the software, along with the data read from the DAQ/motor.\n\n"\
        "Lots of Love,\n"\
        "Philip"
        
        QMessageBox.about(self, "About FTS Controller", msg.strip())    
        
    def on_daq(self):
        msg = "The plot on the screen displays DAQ readings that are constantly being updated. "\
        "To collect data from the DAQ, four parameters need to be specified: the name of the file"\
        " you are writing to, the sampling rate (samples/second), the length of time for which "\
        "you wish to sample, and the channel on the DAQ you want to read from. Once these "\
        "have been specified, press Run, and the data will be saved to a FITS file, after "\
        "the specified time has elapsed."
        
        QMessageBox.about(self, "About DAQ Controls", msg.strip()) 
    
    def on_fw(self):
        msg = "The filter wheel works by specifying which aperture position to display. "\
        "In order to control this, simply type which position (1-6) you want the wheel "\
        "to move to into the position box, then press ENTER."
        
        QMessageBox.about(self, "About Filter Wheel Controls", msg.strip()) 
        
    def on_motor(self):
        msg = "There are two methods of moving the motor: moving it to an exact position, or  "\
        "instructing it to oscillate at a specified frequency and amplitude over a number of cycles. "\
        "The position is specified in mm, and velocity in mm/s. The max velocity is 25 mm /sec, and "\
        "the range of motion is 80 mm. Be sure to enable the axis before using, and then disable it "\
        "when done."
        
        
        QMessageBox.about(self, "About Motor Controls", msg.strip()) 
    
    def closeEvent(self, event):
    
        reply = QMessageBox.question(self, 'Message',
            "Are you sure you want to quit?", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            
            event.accept()
        else:
            event.ignore()  
            
    def create_main_frame(self):
            
        self.main_frame = QWidget()
        self.create_status_bar('Testing')
        self.dpi = 100

        self.setCentralWidget(self.main_frame)
        
            
        
    def create_figure(self,axbox=None,fig_size=(1,1),shareax=None,ax_off=True,disp_coords=True):
        f = Figure(fig_size,self.dpi)
        c = FigureCanvas(f)
        c.setParent(self.main_frame)
        if shareax != None:
            a = f.add_subplot(111,sharex=shareax,sharey=shareax)
        else:
            a = f.add_subplot(111)
        if ax_off:
            a.set_axis_off()
        if axbox!=None:
            a.set_position(axbox) 
        if disp_coords:      
            a.format_coord = lambda x,y:'%i %i'%(x,y)
            t = NavigationToolbar(c,self.main_frame)
        else:
            t = NavigationToolbar(c,self.main_frame,coordinates=False)
        return f,c,a,t
        
    
        
    def create_status_bar(self,text):
        self.status_text = QLabel(text)
        self.statusBar().addWidget(self.status_text)
        
                            
def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()