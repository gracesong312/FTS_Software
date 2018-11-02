import sys, os
import numpy as np
import pyfits
import itertools
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT# as NavigationToolbar
from matplotlib.figure import Figure
from FTS.thorFW102cDriver import FilterWheelDriver
from FTS.NIdaqDriver import MultiChannelAnalogInput
from matplotlib import pyplot as plt
import matplotlib
from matplotlib.figure import Figure
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D
import time
import socket
import threading

import warnings
warnings.filterwarnings("ignore")

from PyDAQmx.DAQmxFunctions import *
from PyDAQmx.DAQmxConstants import *

class MultiChannelAnalogInput():
    """Class to create a multi-channel analog input
    
    Usage: AI = MultiChannelInput(physicalChannel)
        physicalChannel: a string or a list of strings
    optional parameter: limit: tuple or list of tuples, the AI limit values
                        reset: Boolean
    Methods:
        read(name), return the value of the input name
        readAll(), return a dictionary name:value
    """
    def __init__(self,physicalChannel, limit = None, reset = False):
        if type(physicalChannel) == type(""):
            self.physicalChannel = [physicalChannel]
        else:
            self.physicalChannel  =physicalChannel
        self.numberOfChannel = physicalChannel.__len__()
        if limit is None:
            self.limit = dict([(name, (-10.0,10.0)) for name in self.physicalChannel])
        elif type(limit) == tuple:
            self.limit = dict([(name, limit) for name in self.physicalChannel])
        else:
            self.limit = dict([(name, limit[i]) for  i,name in enumerate(self.physicalChannel)])           
        if reset:
            DAQmxResetDevice(physicalChannel[0].split('/')[0] )
    def configure(self):
        # Create one task handle per Channel
        taskHandles = dict([(name,TaskHandle(0)) for name in self.physicalChannel])
        for name in self.physicalChannel:
            DAQmxCreateTask("",byref(taskHandles[name]))
            DAQmxCreateAIVoltageChan(taskHandles[name],name,"",DAQmx_Val_RSE,
                                     self.limit[name][0],self.limit[name][1],
                                     DAQmx_Val_Volts,None)
        self.taskHandles = taskHandles
    def readAll(self):
        return dict([(name,self.read(name)) for name in self.physicalChannel])
    def read(self,name = None):
        if name is None:
            name = self.physicalChannel[0]
        taskHandle = self.taskHandles[name]                    
        DAQmxStartTask(taskHandle)
        data = numpy.zeros((1,), dtype=numpy.float64)
        read = int32()
        DAQmxReadAnalogF64(taskHandle,1,10.0,DAQmx_Val_GroupByChannel,data,1,byref(read),None)
        DAQmxStopTask(taskHandle)
        return data

class NavigationToolbar(NavigationToolbar2QT):
    
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home','Pan', 'Zoom', 'Save')]

    def __init__(self, *args, **kwargs):
        super(NavigationToolbar, self).__init__(*args, **kwargs)
        self.layout().takeAt(4)   
        
class CustomThread(threading.Thread):
    
    def __init__(self,f2,DAQ,DAQ_data,position_data):
        threading.Thread.__init__(self)
        self.paused = False
        self.pause_cond = threading.Condition(threading.Lock())
        self.f2 = f2
        self.DAQ = DAQ
        self.DAQ_data = DAQ_data
        self.position_data = position_data
        self.counter = 40 #Counter only to generate synthetic positions
        
    def addPlotData(self, (valuex,valuey)):
        self.f2.addData(valuex,valuey)

    def run(self):
        while True:
            with self.pause_cond:
                while self.paused:
                    self.pause_cond.wait()

                mySrc = Communicate()
                mySrc.data_signal.connect(self.addPlotData)
                time.sleep(0.001)
                self.DAQ_data.extend(self.DAQ.read())
                pos = 80-80*4*np.abs(np.round((1/160.)*self.counter)-(1/160.)*self.counter)
                self.position_data.extend([pos])
                mySrc.data_signal.emit((self.position_data[-1],self.DAQ_data[-1]))
                self.counter+=.01

    def pause(self):
        self.paused = True
        self.pause_cond.acquire()

    def resume(self):
        self.paused = False
        self.pause_cond.notify()
        self.pause_cond.release()
        
class CustomFigCanvas(FigureCanvas, TimedAnimation):

    def __init__(self):

        self.xdata = []
        self.ydata = []
        
        self.nbins = 160.*100 #divide by speed, multiply by rate
        self.x = np.zeros(self.nbins/4) #Cover 25% of the plot at a time
        self.y = np.zeros(self.nbins/4)
        self.tlen = int(self.nbins/16) #Tail length for highlighting the data

        self.fig,(self.ax1,self.ax2) = plt.subplots(2)
        self.fig.subplots_adjust(hspace=0)
        plt.setp([a.get_xticklabels() for a in self.fig.axes[:-1]], visible=False)

        # self.ax settings
        self.ax2.set_xlabel('Position [mm]',fontsize=18)
        self.fig.text(.09,.5,'Ouptut Voltage',ha='center',va='center',rotation='vertical',fontsize=18)
        self.line1 = Line2D([], [], color='blue')
        self.line1_tail = Line2D([], [], color='red', linewidth=2)
        self.line1_head = Line2D([], [], color='red', marker='o', markeredgecolor='r')
        self.ax1.add_line(self.line1)
        self.ax1.add_line(self.line1_tail)
        self.ax1.add_line(self.line1_head)
        self.line2 = Line2D([], [], color='blue')
        self.line2_tail = Line2D([], [], color='red', linewidth=2)
        self.line2_head = Line2D([], [], color='red', marker='o', markeredgecolor='r')
        self.ax1.add_line(self.line1)
        self.ax1.add_line(self.line1_tail)
        self.ax1.add_line(self.line1_head)
        self.ax2.add_line(self.line2)
        self.ax2.add_line(self.line2_tail)
        self.ax2.add_line(self.line2_head)
        self.ax1.set_xlim(-80,80)
        self.ax2.set_xlim(-80,80)
        self.ax1.set_ylim(-10,10)
        self.ax2.set_ylim(-10,10)
        y1labels = ['','-5','0','5','10']
        self.ax1.set_yticks(np.arange(-10,15,5))
        self.ax1.set_yticklabels(y1labels)
        y2labels = ['-10','-5','0','5','+/-10']
        self.ax2.set_yticks(np.arange(-10,15,5))
        self.ax2.set_yticklabels(y2labels)

        FigureCanvas.__init__(self, self.fig)
        TimedAnimation.__init__(self, self.fig, interval = 10, blit = True)

    def new_frame_seq(self):
        return itertools.count()
        
    def addData(self, valuex,valuey):
        self.xdata.append(valuex)
        self.ydata.append(valuey)
        
    def _init_draw(self):
        lines = [self.line1, self.line1_tail, self.line1_head,self.line2, self.line2_tail, self.line2_head]
        for l in lines:
            l.set_data([], [])

    def _step(self, *args):
        try:
            TimedAnimation._step(self, *args)
        except:
            TimedAnimation._stop(self)
            pass

    def _draw_frame(self, framedata):

        while(len(self.ydata) > 0):
            self.y = np.roll(self.y, -1)
            self.y[-1] = self.ydata[0]
            del(self.ydata[0])

            self.x = np.roll(self.x, -1)
            self.x[-1] = self.xdata[0]
            del(self.xdata[0])
            
            ax1_ind = np.where(np.diff(self.x)>0)[0]
            ax2_ind = np.where(np.diff(self.x)<0)[0]
            
            #Now find the inds in the tail
            ax1_tail_ind = ax1_ind[-1*self.tlen:][np.where(ax1_ind[-1*self.tlen:]>len(self.x)-(self.tlen+2))] #tlen+2 to account for index offsets using np.diff
            ax2_tail_ind = ax2_ind[-1*self.tlen:][np.where(ax2_ind[-1*self.tlen:]>len(self.x)-(self.tlen+2))]
    
            #Plot the base data
            self.line1.set_data(self.x[ax1_ind+1], self.y[ax1_ind+1])
            self.line2.set_data(self.x[ax2_ind+1], self.y[ax2_ind+1])
            
            #Plot the (split) tail
            self.line1_tail.set_data(self.x[ax1_tail_ind+1],self.y[ax1_tail_ind+1]) #+1 to account for index offsets using np.diff
            self.line2_tail.set_data(self.x[ax2_tail_ind+1],self.y[ax2_tail_ind+1])
            
            #Plot the head
            if len(self.x)-2 in ax1_ind:
                self.line1_head.set_data(self.x[-1], self.y[-1])
                self.line2_head.set_data([],[])
            else:
                self.line1_head.set_data([],[])
                self.line2_head.set_data(self.x[-1], self.y[-1])
            
            self._drawn_artists = [self.line1, self.line1_tail, self.line1_head,self.line2, self.line2_tail, self.line2_head]

class Communicate(QObject):
    data_signal = pyqtSignal(tuple)

class Window(QMainWindow):
    
    def __init__(self):
        super(Window,self).__init__()
        self.setWindowTitle('FTS Controller')
        self.setGeometry(0,0,1920,1080)
        self.dpi = 100
        self.icon_direc = 'C:/Users/Philip/Desktop/FTS_Software/Icons/'
        self.general_font = self.create_qfont('Lucidia',12)
        self.setWindowIcon(QIcon(self.icon_direc+'logo.png'))
        self.create_menu()
        self.create_toolbar()
        self.create_main_frame()
        self.show()
        
######################################################################################################################
##########################################  DAQ Functions  ###########################################################
######################################################################################################################    
            
    def on_pause(self):
        if self.pause_btn.isChecked():
            self.dataLoop.pause()
        else:
            self.dataLoop.resume()
    
        
######################################################################################################################
########################################  Motor Functions  ###########################################################
######################################################################################################################

    def find_zopd(self):
        '''
        Function to find and store the zero optical path difference location
        '''
        self.motor.send('HOME X\n') #Find the home position
        command = 'MOVEINC X%.3f XF%.3f\n'%(80,1) #Slew to one end of the axis
        self.motor.send(command)
        self.DAQ_data = []
        self.motorx = []
        command = 'MOVEINC X%.3f XF%.3f\n'%(-160,1) #Slew the entire axis
        self.motor.send(command)
        response = self.motor.recv(1024)
        if response=='%\n':
            self.statusBar().showMessage('Finding zero optical path difference')
        else:
            self.statusBar().showMessage('Error!')
        self.zopd = self.motorx[np.where(self.DAQ_data==np.min(self.DAQ_data))]
        self.statusBar().showMessage('Zero optical path difference found at %0.5f'%self.zopd)
        self.DAQ_data = []
        self.motorx = []
    
    def goto_zopd(self):
        '''
        Function to slew to the zero optical path difference point.
        '''
        try: 
            command = 'MOVEINC X%.3f XF%.3f\n'%(self.zopd,1)
        except:
            self.statusBar().showMessage('Please find zero optical path difference first.')
        self.motor.send(command)
        response = self.motor.recv(1024)
        if response=='%\n':
            self.statusBar().showMessage('Slewing to zero optical path difference')
        else:
            self.statusBar().showMessage('Error!')      


######################################################################################################################
#######################################  Format Functions  ###########################################################
######################################################################################################################        
        
    def add_actions(self,target,actions):
        '''
        Function to add multiple actions to a menu or toolbar at once.  If no action is provide (i.e. action==None)
        then a simple separator is added.
        
        Inputs:
            
            - target: The widget to add the action to
            
            - action: The action to add to the widget
        
        '''
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action) 
                
    def add_space(self,target):
        '''
        Function to add space in between various actions or widgets of the target.  It adds space to expand to fill
        the available size of the target.
        '''
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        target.addWidget(spacer)
        
    
            
    def create_action(self,text,slot=None,shortcut=None,icon=None,
                    tip=None,checkable=False,signal='triggered()',setStatus=False):                
        '''
        Function to create an action to be used in the GUI.  Actions are objects that perform a task when interacted
        with.  Almost all actions in thsi GUI will be signalled by a trigger (i.e. clicked).  Other actions include
        hovering, changing state or toggling (boolean state where checked=False)
        
        Inputs:
            
            - text: Text to appear on the button
            
            - slot: The action to take when triggered.  Usually this points to another function
            
            - shortcut: If provided, the keyboard shortcut can be used
            
            - icon: Either the root name of the image to use (must be a .png file) or a QIcon object.  Only the name
                    of the image is needed, because the directory is automatically applied with self.icon_direc. A 
                    QIcon object permits the use of various images, depending on the state of the action.  All actions
                    in the GUI are enabled, but can either be active or inactive.
                    
            - tip: A string of text to display while hovering over the action
            
            - checkable: Allow the action to be either active or inactive by being pressed
            
            - signal:  The signal to apply to the action.  Either triggered, changed, hovered, or toggled
            
            - setStatus: If true, the status bar is also display the tip string
        '''                                                                    
        action = QAction(text, self)
        if icon is not None:
            if type(icon) is str:
                action.setIcon(QIcon(self.icon_direc+"%s.png" % icon))
            else:
                action.setIcon(icon)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            if setStatus: 
                action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action               


    def create_figure(self,axbox=None,fig_size=(1,1),shareax=None,ax_off=True,disp_coords=True):
        '''
        May be scrapped depending on the development of the GUI
        '''
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
    
            
    def create_main_frame(self):
        '''
        This is the function where all the additional functionality and layout of the GUI is defined.  Every button,
        figure, and action is defined here and displayed using the builtin layout options of PyQt.  This allows for
        dynamic resizing/positioning of the items in the GUI.
        '''
        self.main_frame = QWidget()
        self.create_status_bar('FTS_Software_v1.0')
        
        #Create our various fonts
        title_font = self.create_qfont('Lucidia',16,('underlined',))                
                        
        #Create the input form.  This is a long bit of code, but we use individual layouts to allow
        #for better positioning freedom.
        form = QVBoxLayout()
        form.addStretch()
        
        #First we add the title line
        title1 = self.create_qlabel('Input Parameters',375,20,'center',title_font)
        form.addWidget(title1)
        
        #Add the speed box
        speed_box = QHBoxLayout()
        speed_box.setSpacing(0)
        speed_label = self.create_qlabel('Scan Speed:',120,20,'left',self.general_font)
        self.speed_line = self.create_qline(150,20,font=self.general_font)
        speed_items = ['cm/s','mm/s','um/s']
        self.speed_combo = self.create_qcombobox(speed_items,65,20,self.general_font,1)
        speed_box.addWidget(speed_label)
        speed_box.addWidget(self.speed_line)
        speed_box.addWidget(self.speed_combo)
        speed_box.addStretch()
        form.addLayout(speed_box)
        
        #Add the filter description box
        filtname_box = QHBoxLayout()
        filtname_box.setSpacing(0)
        filtname_label = self.create_qlabel('Filter Name:',120,20,'left',self.general_font)
        self.filtname_line = self.create_qline(215,20,font=self.general_font)
        filtname_box.addWidget(filtname_label)
        filtname_box.addWidget(self.filtname_line)
        filtname_box.addStretch()
        form.addLayout(filtname_box)
        
        #Add the filter position box
        filtpos_box = QHBoxLayout()
        filtpos_box.setSpacing(0)
        filtpos_label = self.create_qlabel('Filter Position:',120,20,'left',self.general_font)
        self.filtpos_combo = QComboBox()
        self.filtpos_combo.addItems(['Position 1','Position 2','Position 3',
                                     'Position 4','Position 5','Posiiton 6'])
        self.filtpos_combo.setFixedWidth(215)
        self.filtpos_combo.setFont(self.general_font)
        filtpos_box.addWidget(filtpos_label)
        filtpos_box.addWidget(self.filtpos_combo)
        filtpos_box.addStretch()
        form.addLayout(filtpos_box)
        
        #Add the distance of the throw box
        throw_box = QHBoxLayout()
        throw_box.setSpacing(0)
        throw_label = self.create_qlabel('Throw Distance:',120,20,'left',self.general_font)
        self.throw_line = self.create_qline(150,20,font=self.general_font)
        throw_items = ['cm','mm','um']
        self.throw_combo = self.create_qcombobox(throw_items,65,20,self.general_font,1)
        throw_box.addWidget(throw_label)
        throw_box.addWidget(self.throw_line)
        throw_box.addWidget(self.throw_combo)
        throw_box.addStretch()
        form.addLayout(throw_box)
        
        #Add the iteration box
        iter_box = QHBoxLayout()
        iter_box.setSpacing(0)
        iter_label = self.create_qlabel('# Iterations:',120,20,'left',self.general_font)
        self.iter_line = self.create_qline(215,20,font=self.general_font)
        iter_box.addWidget(iter_label)
        iter_box.addWidget(self.iter_line)
        iter_box.addStretch()
        form.addLayout(iter_box)
        
        #Add the sample rate box
        rate_box = QHBoxLayout()
        rate_box.setSpacing(0)
        rate_label = self.create_qlabel('Sampling Rate:',120,20,'left',self.general_font)
        self.rate_line = self.create_qline(150,20,font=self.general_font)
        rate_items = ['kHz','Hz']
        self.rate_combo = self.create_qcombobox(rate_items,65,20,self.general_font,1)
        rate_box.addWidget(rate_label)
        rate_box.addWidget(self.rate_line)
        rate_box.addWidget(self.rate_combo)
        rate_box.addStretch()
        form.addLayout(rate_box)
        
        #Add the chopper speed box
        chopper_box = QHBoxLayout()
        chopper_box.setSpacing(0)
        chopper_label = self.create_qlabel('Chop Rate:',120,20,'left',self.general_font)
        self.chopper_line = self.create_qline(150,20,font=self.general_font)
        chopper_box.addWidget(chopper_label)
        chopper_box.addWidget(self.chopper_line)
        chopper_box.addWidget(self.create_qlabel(' [Hz]',120,20,'left',self.general_font))
        chopper_box.addStretch()
        form.addLayout(chopper_box)        
        
        #Add the save file box
        save_box = QHBoxLayout()
        save_box.setSpacing(0)
        save_label = self.create_qlabel('Save File:',120,20,'left',self.general_font)
        self.save_line = self.create_qline(150,20,font=self.general_font)
        self.selectSave_btn = self.create_qpushbutton('Select',self.open_save,width=65,height=22,font=self.general_font)
        save_box.addWidget(save_label)
        save_box.addWidget(self.save_line)
        save_box.addWidget(self.selectSave_btn)
        save_box.addStretch()
        form.addLayout(save_box)
        
        #Add the source description box
        source_box = QHBoxLayout()
        source_box.setSpacing(0)
        source_label = self.create_qlabel('Source:',120,20,'left',self.general_font)
        self.source_line = self.create_qline(120,20,font=self.general_font)
        source_box.addWidget(source_label)
        source_box.addWidget(self.source_line)
        source_box.addWidget(self.create_qlabel(' @ ',30,20,'left',self.general_font))
        self.source_temp_line = self.create_qline(45,20,font=self.general_font)
        source_box.addWidget(self.source_temp_line)
        source_box.addWidget(self.create_qlabel(' K',20,20,'left',self.general_font))
        source_box.addStretch()
        form.addLayout(source_box)
        
        #Add the detector pressure box
        #Will be used to convert to temperature
        press_box = QHBoxLayout()
        press_box.setSpacing(0)
        press_label = self.create_qlabel('Detect Press:',120,20,'left',self.general_font)
        self.press_line = self.create_qline(155,20,font=self.general_font)
        press_box.addWidget(press_label)
        press_box.addWidget(self.press_line)
        press_box.addWidget(self.create_qlabel(' mbar',60,20,'left',self.general_font))
        press_box.addStretch()
        form.addLayout(press_box)
        
        #Add the lock-in sensitivity box
        li_sens_box = QHBoxLayout()
        li_sens_box.setSpacing(0)
        li_sens_label = self.create_qlabel('LI Sensitivity:',120,20,'left',self.general_font)
        self.li_sens_line = self.create_qline(150,20,font=self.general_font)
        li_sens_items = ['V','mV','uV','nV']
        self.li_sens_combo = self.create_qcombobox(li_sens_items,65,20,self.general_font,1)
        li_sens_box.addWidget(li_sens_label)
        li_sens_box.addWidget(self.li_sens_line)
        li_sens_box.addWidget(self.li_sens_combo)
        li_sens_box.addStretch()
        form.addLayout(li_sens_box)
        
        #Add the lock-in time constant box
        li_time_box = QHBoxLayout()
        li_time_box.setSpacing(0)
        li_time_label = self.create_qlabel('LI Time Const:',120,20,'left',self.general_font)
        self.li_time_line = self.create_qline(150,20,font=self.general_font)
        li_time_items = ['ks','s','ms','us']
        self.li_time_combo = self.create_qcombobox(li_time_items,65,20,self.general_font,2)
        li_time_box.addWidget(li_time_label)
        li_time_box.addWidget(self.li_time_line)
        li_time_box.addWidget(self.li_time_combo)
        li_time_box.addStretch()
        form.addLayout(li_time_box)
        
        #Space to look nice
        form.addSpacing(50)
        
        #Create the buttons
        self.clear_btn = self.create_qpushbutton('Clear',self.do_nothing,height=25,font=self.general_font)
        self.abort_btn = self.create_qpushbutton('Abort',self.do_nothing,height=25,font=self.general_font)        
        self.submit_btn = self.create_qpushbutton('Submit',self.on_submit,height=25,font=self.general_font)
        self.pause_btn = self.create_qpushbutton('Pause',self.on_pause,height=25,font=self.general_font,checkable=True)
        self.find_zopd_btn = self.create_qpushbutton('Find ZOPD',self.do_nothing,height=25,font=self.general_font)        
        self.goto_zopd_btn = self.create_qpushbutton('Go To ZOPD',self.do_nothing,height=25,font=self.general_font)
                
        
        btn_box1 = QHBoxLayout()
        btn_box1.addWidget(self.clear_btn)
        btn_box1.addWidget(self.submit_btn)
        form.addLayout(btn_box1)  
        
        #Create the second button row

        btn_box2 = QHBoxLayout()
        btn_box2.addWidget(self.pause_btn)
        btn_box2.addWidget(self.abort_btn)
        form.addLayout(btn_box2) 
        
        btn_box3 = QHBoxLayout()
        btn_box3.addWidget(self.find_zopd_btn)
        btn_box3.addWidget(self.goto_zopd_btn)
        form.addLayout(btn_box3) 
        
        form.addStretch()
        
        #Next we create the figures
        self.f1,self.c1,self.a1,self.t1 = self.create_figure(axbox=[.025,.06,.95,.9],fig_size=(16,4),ax_off=False,disp_coords=False)
        self.f2 = CustomFigCanvas()
        #self.f2,self.c2,self.a2,self.t2 = self.create_figure(axbox=[.025,.06,.95,.9],fig_size=(16,4),ax_off=False,disp_coords=False)
        #self.a2.set_axis_bgcolor((1, 1, 1))
        
        figs = QVBoxLayout()
        figs.addWidget(self.t1)
        figs.addWidget(self.c1)
        figs.addWidget(self.f2)
        #figs.addWidget(self.t2)
        #figs.addWidget(self.c2)
        
        #Add the rest of the layouts
        final_layout = QHBoxLayout()
        final_layout.addLayout(form)
        final_layout.addSpacing(12)
        final_layout.addLayout(figs)

        #Set the GUI in the main frame
        self.main_frame.setLayout(final_layout)        
        self.setCentralWidget(self.main_frame)
        

    
    def create_menu(self):
        '''
        Function to create the menu bar.  The menu bar typically takes actions that are words, such as 'Save As', but
        can also take pictures, if desired.  Shortcuts for the actions are displayed with the action itself.
        
        Here we add a file menu that can either save or quit and an about menu to provide details of the software.
        '''
        mainMenu = self.menuBar()
        
        fileMenu = mainMenu.addMenu('&File')
        
        quit_action = self.create_action('&Quit', slot=self.close, 
            shortcut='Ctrl+Q', tip='Close the application')
            
        save_action = self.create_action('&Save As', slot=self.save,
            shortcut='Ctrl+S',tip='Save the current output')
                
        self.add_actions(fileMenu,(quit_action,save_action,))
        
        helpMenu = mainMenu.addMenu('&Help')
        
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, tip='About FTS Controller')
        
        self.add_actions(helpMenu, (about_action,))
        
        
    def create_qcombobox(self,items,width=None,height=None,font=None,start_ind=None):
        '''
        Function to create a QComboBox object
        
        Inputs:
            
            - items: The list of labels to be included in the combo box
            
            - width: The width of the combo box
            
            - height: The height of the combo box
            
            - font: The font to be used on the items in the combo box
            
            - start_ind: The starting index (i.e. item in the list) for the combo box
        '''
        combo = QComboBox()
        combo.addItems(items)
        if width is not None:
            combo.setFixedWidth(width)
        if height is not None:
            combo.setFixedHeight(height)
        if font is not None:
            combo.setFont(font)
        if start_ind is not None:
            combo.setCurrentIndex(start_ind)
            
        return combo
        
        
    def create_qfont(self,font,size=None,formats=None):
        '''
        Function to create a font object to be used throughout the GUI.  Possible options
        are font type, size, and format.
        
        Inputs:
            
            - font: String of the font to use for the QFont object
            
            - size: Size of the font to be used.
            
            - formats: List of formats for the label.  Either italic, bold, or underlined.
        '''
        qfont = QFont(font)
        if size is not None:
            qfont.setPointSize(size)
        if formats is not None:
            for format in formats:
                if format=='italic':
                    qfont.setItalic(True)
                elif format=='bold':
                    qfont.setBold(True)
                elif format=='underlined':
                    qfont.setUnderline(True)
                else:
                    pass
        return qfont
        
          
    def create_qicon(self,on,off):
        '''
        Function to create a QIcon object to be used with the create_action function.
        
        Inputs:
            
            - on: Root name of the image to be used when the action is in an active state
            
            - off: Root name of the image to be used when the action is in a disabled state
        '''
        qicon = QIcon()
        qicon.addPixmap(QPixmap(self.icon_direc+"%s.png" % on),
                        QIcon.Normal, QIcon.On)
        qicon.addPixmap(QPixmap(self.icon_direc+"%s.png" % off),
                        QIcon.Normal, QIcon.Off)
        return qicon
     
           
    def create_qlabel(self,text,width=None,height=None,alignment=None,font=None,style=None):
        '''
        Function to create a QLabel object to be used the for the parameter
        input form. since most parameters will use this format.  It defaults to the parent
        spacings, if they are not defined.
        
        Inputs:
            
            - text - The text to be displayed on the label
            
            - width - The width of the button
            
            - height - The height of the button
            
            - alignment - 'left', 'center', or 'right'
            
            - font - The QFont object to be used
            
            - style - The style string to be used
        '''
        qlabel = QLabel(text)
        qline = QLineEdit()
        if width is not None:
            qlabel.setFixedWidth(width)
            qline.setFixedWidth(width)
        if height is not None:
            qlabel.setFixedHeight(height)
            qline.setFixedHeight(height)
        if alignment is not None:
            if alignment == 'right':
                qlabel.setAlignment(Qt.AlignRight)
            elif alignment == 'left':
                qlabel.setAlignment(Qt.AlignLeft)
            elif alignment =='center':
                qlabel.setAlignment(Qt.AlignCenter)
            else:
                pass
        if font is not None:
            qlabel.setFont(font)
        if style is not None:
            qlabel.setStyleSheet(style)
            
        return qlabel     
     
    def create_qline(self,width=None,height=None,font=None,style=None):
        '''
        Simple function to make a QLineEdit object of a given width and height.
        
        Inputs:
            
            - width: The width of the QLineEdit field
            
            - height: The height of the QLineEdit field
            
            - font: The font to be used in the QLineEdit field
            
            - style: String of the style for the QLineEdit field
        '''
        
        qline = QLineEdit()
        if width is not None:
            qline.setFixedWidth(width)
        qline.setFixedHeight(height)
        if font is not None:
            qline.setFont(font)
        if style is not None:
            qline.setStyleSheet(style)
        
        return qline
        
    def create_qpushbutton(self,text, slot, width=None,height=None,font=None,style=None,
                            checkable=False, return_type=None):
        '''
        Another simple function to make a QPushButton object, with given stylistic inputs
        
        Inputs:
            
            - text: The text to be displayed on the button
            
            - slot: The function that is called when the button is pressed
            
            - width: The width of the button
            
            - height: The height of the button
            
            - font: The font to be used on the button
            
            - style: String of the style to be used for the button
            
            - checkable: Sets whether or not the button is checkable (i.e. if the state can be held)
            
            - return_type: Overwrites the default return type of the button.  Either int, str, float,
                           or bool are accepted.  The most common use will be to state whether that a
                           checkable button should return a boolean. (True is enabled, False if disabled)
        '''
        qpushbutton = QPushButton(text)
        if width is not None:
            qpushbutton.setFixedWidth(width)
        if height is not None:
            qpushbutton.setFixedHeight(height)
        if font is not None:
            qpushbutton.setFont(font)
        if style is not None:
            qpushbutton.setStyleSheet(style)
        if checkable is not False:
            qpushbutton.setCheckable(True)
        if return_type is not None:
            qpushbutton.clicked[return_type].connect(slot)
        else:
            qpushbutton.clicked.connect(slot)
        
        return qpushbutton
     
        
    def create_status_bar(self,text):
        '''
        Very simple function to create the initial status bar and to display action tips.
        
        Inputs:
            
            - text: The text to be displayed on the status bar.
        '''
        self.status_text = QLabel(text)
        self.statusBar().addWidget(self.status_text)
        
                 
    def create_toolbar(self):
        '''
        Function to create the top toolbar functionality.  All actions are linked to functions defined below in the
        toolbar functions section of the code.
        '''

        #Create the toolbar
        self.toolbar = self.addToolBar('Tools')
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet('QToolBar{spacing:6px;}')

        #Add the connection group
        self.connect_btn = self.create_action('connect',slot=self.connect_motor,
            icon='connect',shortcut='Ctrl+F', tip='Connect motor')
            
        self.disconnect_btn = self.create_action('disconnect',slot=self.disconnect_motor,
            icon='disconnect',shortcut='Ctrl+G',tip='Disconnect motor')
            
        self.home_btn = self.create_action('home',slot=self.send_home,
            icon='home',shortcut='Ctrl+H', tip='Return motor to home position')
            
        self.enable_icon = self.create_qicon('enable','idle')
        self.enable_btn = self.create_action('enable',slot=self.enable_motor,
            icon=self.enable_icon,shortcut='Ctrl+E', tip='Enable motor axis',checkable=True)
            
        self.disable_icon = self.create_qicon('disable','idle')
        self.disable_btn = self.create_action('disable',slot=self.disable_motor,
            icon=self.disable_icon,shortcut='Ctrl+D', tip='Disable motor axis', checkable=True)
            
            
        self.add_actions(self.toolbar,(self.connect_btn, self.disconnect_btn,
                                        None, self.home_btn, self.enable_btn,
                                        self.disable_btn))
                      
        #Add the status group                      
        self.toolbar.addWidget(self.create_qlabel('Status:',font=self.general_font))
        self.motor_status = self.create_qlabel('IDLE',width=100,alignment='center',font=self.general_font,
                                            style='color: black; background-color: rgb(211,211,211); border: 2px solid black')
        self.toolbar.addWidget(self.motor_status)
        
        #Spacing for aesthetics
        self.add_space(self.toolbar)

        #Add the motion group
        self.toolbar.addWidget(self.create_qlabel('Jog:',font=self.general_font))
        self.motor_dist = QLineEdit()
        self.motor_dist.setFixedWidth(50)
        self.toolbar.addWidget(self.motor_dist)
        self.toolbar.addWidget(self.create_qlabel('mm',font=self.general_font))
        '''
        dist_items = ['mm','cm']
        self.toolbar_dist_combo = self.create_qcombobox(dist_items,65,20,self.general_font,0)
        self.toolbar.addWidget(self.toolbar_dist_combo)        
        '''
        self.motor_speed = QLineEdit()
        self.motor_speed.setFixedWidth(50)
        self.toolbar.addWidget(self.motor_speed)
        self.toolbar.addWidget(self.create_qlabel('mm/s',font=self.general_font))
        '''
        speed_items = ['cm/s','mm/s','um/s']
        self.toolbar_speed_combo = self.create_qcombobox(speed_items,65,20,self.general_font,1)
        self.toolbar.addWidget(self.toolbar_speed_combo)
        '''
        self.left_jog_btn = self.create_action('left',slot=self.jog_left,
            icon='left',shortcut='Ctrl+K', tip='Jog the motor left at the defined speed')
        self.right_jog_btn = self.create_action('right',slot=self.jog_right,
            icon='right',shortcut='Ctrl+K', tip='Jog the motor right at the defined speed')
        self.add_actions(self.toolbar,(self.left_jog_btn,self.right_jog_btn,None,))
        
        self.toolbar.addWidget(self.create_qlabel('Position:',font=self.general_font))
        self.position = 0.0
        self.position_box = self.create_qlabel('%.5f mm'%self.position,width=120,alignment='center',
                                font=QFont('Lucidia',12),style='color: yellow; background-color: black')
        self.toolbar.addWidget(self.position_box)
        
        #Spacing for aesthetics
        self.add_space(self.toolbar)
        
        #Add the command group
        self.toolbar.addWidget(self.create_qlabel('Command:',font=self.general_font))
        self.command_line = QLineEdit()
        self.command_line.setFixedWidth(150)
        self.toolbar.addWidget(self.command_line)
        
        self.run_btn = self.create_action('run',slot=self.send_command,
            icon='run',shortcut='Ctrl+R', tip='Run the current command line')
            
        self.abort_btn = self.create_action('abort',slot=self.send_abort,
            icon='abort',shortcut='Ctrl+A', tip='Abort the current command')

        self.add_actions(self.toolbar,(self.run_btn,self.abort_btn,))
    
######################################################################################################################
#######################################  Toolbar Functions  ##########################################################
######################################################################################################################   
                                        
                                                                                
                                                                                                                                                                
    def connect_motor(self):
        self.HOST = '192.168.1.2' #Host address
        self.PORT = 8000 #port number for socket
            
        self.motor = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Init socket (TCP/IP)
        self.motor.connect((self.HOST,self.PORT)) #Bind HOST,PORT to socket
        self.motor_status.setText('CONNECTED')
        self.motor_status.setStyleSheet('color: black; background-color: rgb(211,211,211); border: 2px solid black')
        self.statusBar().showMessage('Motor connected.')
        
          
    def disconnect_motor(self):
        self.enable_btn.setChecked(False)
        self.disable_btn.setChecked(False)      
        self.motor_status.setText('IDLE')
        self.motor_status.setStyleSheet('color: black; background-color: rgb(211,211,211); border: 2px solid black')
        self.motor.close()
        self.statusBar().showMessage('Motor connection closed.')
                                      
    def enable_motor(self):
        self.motor.send('ENABLE X\n') #Send enable command
        response = self.motor.recv(1024) #Collect and print response
        if response=='%\n':
            self.enable_btn.setChecked(True)
            self.disable_btn.setChecked(False)
            self.motor_status.setText('ENABLED')
            self.motor_status.setStyleSheet('color: black; background-color: rgb(0,211,0); border: 2px solid black')
            self.statusBar().showMessage('Motor succesfully enabled.')
            motorLoop = threading.Thread(name = 'motorLoop', target = self.read_motor, args = ())
            motorLoop.start()

        else:
             self.statusBar().showMessage('Error!')
             
    def read_motor(self):
        while True:
            time.sleep(.1)
            self.motor.send('PFBK(X)\n')
            self.position = float(self.motor.recv(1024).strip()[1:])  
            self.position_box.setText('%.5f mm'%self.position)
                         
    def disable_motor(self):
        self.motor.send('DISABLE X\n') #Send enable command
        response = self.motor.recv(1024) #Collect and print response
        if response=='%\n':
            self.disable_btn.setChecked(True)
            self.enable_btn.setChecked(False)
            self.motor_status.setText('DISABLED')
            self.motor_status.setStyleSheet('color: black; background-color: rgb(255,0,0); border: 2px solid black')
            self.statusBar().showMessage('Motor succesfully disabled.')
        else:
             self.statusBar().showMessage('Error!')
             
    def send_command(self):
        self.motor.send(self.command_line.text()+'\n')
        response = self.motor.recv(1024)
        if response=='%\n':
            self.statusBar().showMessage('Executing command')
        else:
            self.statusBar().showMessage('Error!')
            
    def send_abort(self):
        self.motor.send('ABORT X\n')
        response = self.motor.recv(1024)
        if response=='%\n':
            self.statusBar().showMessage('Error!')
            
    def send_home(self):
        self.motor.send('HOME X\n')
        response = self.motor.recv(1024)
        if response=='%\n':
            self.statusBar().showMessage('Error!')
            
    def jog_left(self):
        try:
            dist = float(self.motor_dist.text())
            speed = float(self.motor_speed.text())
        except:
            self.statusBar.showMessage('Please enter a valid distance and/or speed')
        if dist<0:
            self.statusBar.showMessage('Speed must be positive when using the toolbar')
        else:
            command = 'MOVEINC X%.3f XF%.3f\n'%(dist,speed)
            self.motor.send(command)
            response = self.motor.recv(1024)
            if response=='%\n':
                self.statusBar().showMessage('Executing jog')
            else:
                self.statusBar().showMessage('Error!')            

    def jog_right(self):
        try:
            dist = float(self.motor_dist.text())
            speed = float(self.motor_speed.text())
        except:
            self.statusBar.showMessage('Please enter a valid distance and/or speed')
        if dist<0:
            self.statusBar.showMessage('Speed must be positive when using the toolbar')
        else:
            command = 'MOVEINC X-%.3f XF%.3f\n'%(dist,speed)
            self.motor.send(command)
            response = self.motor.recv(1024)
            if response=='%\n':
                self.statusBar().showMessage('Executing jog')
            else:
                self.statusBar().showMessage('Error!')         
    
    def do_nothing(self):
        pass      
    

######################################################################################################################
###########################################  Menu Functions  #########################################################
######################################################################################################################

        
    def on_about(self):
        msg = "This software is designed to communicate with the FTS system, specifically "\
        "with the NI USB-6002 DAQ, FW102C Thor Labs filter wheel, IR Labs bolometer, "\
        "CES100-04 blackbody, & Aerotech ANT-160-L linear motor.  Additional "\
        "components can easily be added, with the appropriate drivers.\n\n"\
        "The save menu currently outputs a FITS file containing all the parameters "\
        "stored in the software, along with the data read from the DAQ\\motor."
        
        QMessageBox.about(self, "About FTS Controller", msg.strip())    
        
    def closeEvent(self, event):
        
        reply = QMessageBox.question(self, 'Message',
            "Are you sure you want to quit?", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            
            event.accept()
        else:
            event.ignore()  
            
    def save(self):
        fname = str(QFileDialog.getSaveFileName(self,'Select Save File'))
        #Make sure there is the appropriate extension
        if fname=='':
            num_files = glob.glob('C:/Users/Philip/Desktop/FTS_Software/Data/default_fname_*.fits')
            fname = 'C:/Users/Philip/Desktop/FTS_Software/Data/defaul_fname_%03i.fits'%num_files
        elif fname.endswith('.fits'):
            self.write_fits(fname)
        else:
            QMessageBox.warning(self, 'Error', 'Please provide a .fits extension')
            self.save()
                  
    def write_fits(self,fname):
        
        #Now write the FITS file
        prihdr = pyfits.Header()
        prihdr['NPOINTS'] = (len(self.DAQ_data),'Number of sampled points')
        prihdr['SOURCE'] = (self.source, 'Name of the source used.')
        prihdr['SOURCE TEMP'] = (self.temperature,'Temperature of the source used')
        prihdr['SPEED'] = (self.speed,'Speed of the motor in '+self.speed_combo.currentText())        
        prihdr['FILTER'] = (self.filtname_line.text(),'Description of the filter used.')
        prihdr['DISTANCE'] = (self.throw,'Length of the mirror throw in '+self.throw_combo.currentText())
        prihdr['NITERS'] = (int(self.iter_line.text()),'Number of throw iterations')
        prihdr['RATE'] = (self.rate,'Sampling rate in '+self.rate_combo.currentText())
        prihdr['TIME CONSTANT'] = (self.t_const,'Time constant of the lock-in amplifier')
        prihdr['CHOPPER'] = (self.chopper, 'Chopping frequency in Hz')
        prihdr['DATE'] = (self.date, 'Date when the scan was completed')
        prihdr['START TIME'] = (self.start, 'Time at the beginning of the scan')
        prihdr['PRESSURE'] = 'Detector pressure at the start of the scan'
        prihdr['DETECTOR TEMP'] = 'Detector temperature at the start of the scan'
        prihdr['SENSITIVITY'] = 'Sensitivity of the lock-in amplifier'
        prihdr['TIME CONSTANT'] = 'Time constant of the lock-in amplifier'
        prihdr['GAIN'] = 'Gain on the cryostat'
        prihdr['PREAMP'] = 'Flag for if preamp on cryostat was on or off'
        prihdr['END TIME'] = (self.end, 'Time at the end of the scan')
        prihdr['COMMENT'] = ''
        prihdr['COMMENT'] = 'File was compiled using the FTS_Controller software.'
        prihdr['COMMENT'] = 'Unless otherwise provided a filename, data is stored in'
        prihdr['COMMENT'] = 'C:/Users/Philip/FTS_Software/Data/'
        prihdr['COMMENT'] = 'A number is sequentially appended to the end of each file name.'
        prihdr['COMMENT'] = 'Any item not completed on the form is filled as N/A.'
        prihdr['COMMENT'] = 'The primary HDU stores only the header information for the file.'
        prihdr['COMMENT'] = 'Data is stored as ASCII table extensions in the remaining HDUs.'
        prihdr['COMMENT'] = 'The first column is the position vector for the background scan.'
        prihdr['COMMENT'] = 'The second column is the counts vector for the background scan.'
        prihdr['COMMENT'] = 'The third column is the position vector for the filter scan.'
        prihdr['COMMENT'] = 'The fourth column is the counts vector for the filter scan.'
        prihdr['COMMENT'] = 'The fifth column is the calculated transmission.'
        prihdr['COMMENT'] = ''
        prihdr['COMMENT'] = 'Intermediate values of the transmission vector are not stored.'
        prihdr['COMMENT'] = 'However they can be found from the following:'
        prihdr['COMMENT'] = 'Steps'
        prihdr['COMMENT'] = 'to'
        prihdr['COMMENT'] = 'completing'
        prihdr['COMMENT'] = 'the'
        prihdr['COMMENT'] = 'Fourier'
        prihdr['COMMENT'] = 'Transform'

        
        prihdu = pyfits.PrimaryHDU(header=prihdr)
        
        xbhdu = pyfits.TableHDU.from_columns(
                [pyfits.Column(name='X_bkgd',format='E15.7',array=self.position_bkgd)])
        ybhdu = pyfits.TableHDU.from_columns(
                [pyfits.Column(name='Y_bkgd',format='E15.7',array=self.DAQ_bkgd)])
        xdhdu = pyfits.TableHDU.from_columns(
                [pyfits.Column(name='X_data',format='E15.7',array=self.position_data)])
        ydhdu = pyfits.TableHDU.from_columns(
                [pyfits.Column(name='Y_data',format='E15.7',array=self.DAQ_data)])
        thdu = pyfits.TableHDU.from_columns(
                [pyfits.Column(name='Transmission',format='E15.7',array=self.trans)])
        
        hdulist = pyfits.HDUList([prihdu,xbhdu,ybhdu,xdhdu,ydhdu,thdu])
        hdulist.writeto(self.fname,clobber=True)
            

######################################################################################################################
###########################################  GUI Functions  ##########################################################
######################################################################################################################   
    def position_filter(self):
        filt_wheel = FilterWheelDriver(p=0,baud=115200)
        filt_wheel.setPos(int(self.filtpos_combo.currentText()[-1]))
        filt_wheel.close()
        
    def systems_check(self):
        '''
        Function to check the connections of all the components and make sure
        everything is set up properly.
        '''
        

    def open_save(self):
        
        directory = QFileDialog.getSaveFileName(self,'Select Save File')
        self.save_line.setText(directory.replace('\\','\\'))
        
    def start_stepper(self):
        if self.ser.isOpen() == False:
            self.ser.open()
        self.ser.write(chr(250))
        
    def stop_stepper(self):
        self.ser.close()
        self.ser.open()
                
    def on_submit(self):
        
        #Electrical checks - ensure that all components are connected and responding
        
        #Chopper
        try:
            pass#self.ser = serial.Serial('COM5',9600,timeout = 1)
        except:
            pass
        
        #DAQ
        
        #Motor
        
        #Filter wheel
        try:
            pass#self.position_filter()
        except:
            pass#self.statusBar().showMessage('Please check the filter wheel connection.')
        
        #Other
        self.DAQ_data = []
        self.position_data = []
        channel = ["Dev1/ai0"]
        self.DAQ = MultiChannelAnalogInput(channel)
        self.DAQ.configure()
        self.dataLoop = CustomThread(self.f2,self.DAQ,self.DAQ_data,self.position_data)
        self.dataLoop.start()
        #self.position_filter()


        
                            
def main():
    app = QApplication(sys.argv)
    window = Window()
    window.showMaximized()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()