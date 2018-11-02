import sys, os
import numpy as np
import pyfits
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
import threading
import serial

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
        
class CustomFigCanvas(FigureCanvas, TimedAnimation):

    def __init__(self):

        self.addedData = []

        # The data
        self.xlim = 200
        self.n = np.linspace(0, self.xlim - 1, self.xlim)
        a = []
        b = []
        a.append(2.0)
        a.append(4.0)
        a.append(2.0)
        b.append(4.0)
        b.append(3.0)
        b.append(4.0)
        self.y = (self.n * 0.0) + 50

        # The window
        self.fig = Figure(figsize=(5,5), dpi=100)
        self.ax1 = self.fig.add_subplot(111)


        # self.ax1 settings
        self.ax1.set_xlabel('time')
        self.ax1.set_ylabel('raw data')
        self.line1 = Line2D([], [], color='blue')
        self.line1_tail = Line2D([], [], color='red', linewidth=2)
        self.line1_head = Line2D([], [], color='red', marker='o', markeredgecolor='r')
        self.ax1.add_line(self.line1)
        self.ax1.add_line(self.line1_tail)
        self.ax1.add_line(self.line1_head)
        self.ax1.set_xlim(0, self.xlim - 1)
        self.ax1.set_ylim(-10,10)


        FigureCanvas.__init__(self, self.fig)
        TimedAnimation.__init__(self, self.fig, interval = 50, blit = True)

    def new_frame_seq(self):
        return iter(range(self.n.size))

    def _init_draw(self):
        lines = [self.line1, self.line1_tail, self.line1_head]
        for l in lines:
            l.set_data([], [])

    def addData(self, value):
        self.addedData.append(value)

    def zoomIn(self, value):
        bottom = self.ax1.get_ylim()[0]
        top = self.ax1.get_ylim()[1]
        bottom += value
        top -= value
        self.ax1.set_ylim(bottom,top)
        self.draw()


    def _step(self, *args):
        # Extends the _step() method for the TimedAnimation class.
        try:
            TimedAnimation._step(self, *args)
        except Exception as e:
            self.abc += 1
            print(str(self.abc))
            TimedAnimation._stop(self)
            pass

    def _draw_frame(self, framedata):
        margin = 2
        while(len(self.addedData) > 0):
            self.y = np.roll(self.y, -1)
            self.y[-1] = self.addedData[0]
            del(self.addedData[0])


        self.line1.set_data(self.n[ 0 : self.n.size - margin ], self.y[ 0 : self.n.size - margin ])
        self.line1_tail.set_data(np.append(self.n[-10:-1 - margin], self.n[-1 - margin]), np.append(self.y[-10:-1 - margin], self.y[-1 - margin]))
        self.line1_head.set_data(self.n[-1 - margin], self.y[-1 - margin])
        self._drawn_artists = [self.line1, self.line1_tail, self.line1_head]

class Communicate(QObject):
    data_signal = pyqtSignal(float)

class Window(QMainWindow):
    
    def __init__(self):
        super(Window,self).__init__()
        self.setWindowTitle('FTS Controller')
        self.setGeometry(0,0,1920,1080)
        self.dpi = 100
        self.icon_direc = 'C:\\Users\\Philip\\Desktop\\FTS_Software\\Icons\\'
        self.general_font = self.create_qfont('Lucidia',12)
        self.setWindowIcon(QIcon(self.icon_direc+'logo.png'))
        self.create_menu()
        self.create_toolbar()
        self.create_main_frame()
        self.DAQx = []
        channel = ["Dev2/ai0"]
        self.DAQ = MultiChannelAnalogInput(channel)
        self.DAQ.configure()
        plotLoop = threading.Thread(name = 'plotLoop', target = self.read_DAQ, args = ())
        plotLoop.start()
        DAQLoop = threading.Thread(name = 'DAQLoop', target = self.dataSendLoop, args = (self.addData_callbackFunc,))
        DAQLoop.start()
        self.show()
        
    def read_DAQ(self):
        while True:
            time.sleep(.01)
            self.DAQx.extend(self.DAQ.read())
        
    def dataSendLoop(self, addData_callbackFunc):
        # Setup the signal-slot mechanism.
        mySrc = Communicate()
        mySrc.data_signal.connect(addData_callbackFunc)
    
        while(True):
            time.sleep(0.1)
            mySrc.data_signal.emit(self.DAQx[-1]) # <- Here you emit a signal!
        
    def addData_callbackFunc(self, value):
        self.f2.addData(value)

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
        title = self.create_qlabel('Input Parameters',270,20,'center',title_font)
        form.addWidget(title)
        
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
        iter_label = self.create_qlabel('# Iterations:',120,20,'lefr',self.general_font)
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
        
        #Create the final button box
        self.clear_btn = self.create_qpushbutton('Clear',self.do_nothing,height=25,font=self.general_font)
        self.abort_btn = self.create_qpushbutton('Abort',self.do_nothing,height=25,font=self.general_font)        
        self.submit_btn = self.create_qpushbutton('Submit',self.on_submit,height=25,font=self.general_font)
        self.chop_btn = self.create_qpushbutton('Chop',self.start_stepper,height= 25,font = self.general_font)
        self.stop_btn = self.create_qpushbutton('Stop',self.stop_stepper,height= 25,font = self.general_font)
        
        
        btn_box = QHBoxLayout()
        btn_box.addWidget(self.clear_btn)
        btn_box.addWidget(self.abort_btn)
        btn_box.addWidget(self.submit_btn)
        btn_box.addWidget(self.chop_btn)
        btn_box.addWidget(self.stop_btn)
        form.addLayout(btn_box)
        
        
        #Add spacing to center the form
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
        self.ser = serial.Serial('COM3',9600,timeout = 1)

        #Add the connection group
        self.connect_btn = self.create_action('connect',slot=self.connect_motor,
            icon='connect',shortcut='Ctrl+F', tip='Connect motor')
            
        self.disconnect_btn = self.create_action('disconnect',slot=self.disconnect_motor,
            icon='disconnect',shortcut='Ctrl+G',tip='Disconnect motor')
            
        self.home_btn = self.create_action('home',slot=self.do_nothing,
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
        self.motor_speed = QLineEdit()
        self.motor_speed.setFixedWidth(100)
        self.toolbar.addWidget(self.motor_speed)
        
        speed_items = ['cm/s','mm/s','um/s']
        self.toolbar_combo = self.create_qcombobox(speed_items,65,20,self.general_font,1)
        self.toolbar.addWidget(self.toolbar_combo)
        
        self.left_jog_btn = self.create_action('left',slot=self.do_nothing,
            icon='left',shortcut='Ctrl+K', tip='Jog the motor left at the defined speed')
        self.right_jog_btn = self.create_action('right',slot=self.do_nothing,
            icon='right',shortcut='Ctrl+K', tip='Jog the motor right at the defined speed')
        self.add_actions(self.toolbar,(self.left_jog_btn,self.right_jog_btn,None,))
        
        self.toolbar.addWidget(self.create_qlabel('Position:',font=self.general_font))
        self.position = 0.0
        self.position_box = self.create_qlabel('%.4f mm/s'%self.position,width=120,alignment='center',
                                font=QFont('Lucidia',12),style='color: yellow; background-color: black')
        self.toolbar.addWidget(self.position_box)
        
        #Spacing for aesthetics
        self.add_space(self.toolbar)
        
        #Add the command group
        self.toolbar.addWidget(self.create_qlabel('Command:',font=self.general_font))
        self.command_line = QLineEdit()
        self.command_line.setFixedWidth(250)
        self.toolbar.addWidget(self.command_line)
        
        self.run_btn = self.create_action('run',slot=self.do_nothing,
            icon='run',shortcut='Ctrl+R', tip='Run the current command line')
            
        self.abort_btn = self.create_action('abort',slot=self.do_nothing,
            icon='abort',shortcut='Ctrl+A', tip='Abort the current command')

        self.add_actions(self.toolbar,(self.run_btn,self.abort_btn,))
    
######################################################################################################################
#######################################  Toolbar Functions  ##########################################################
######################################################################################################################   
                                        
                                                                                
                                                                                                                                                                
    def connect_motor(self):
        self.enable_btn.setChecked(True)
        self.motor_status.setText('ENABLED')
        self.motor_status.setStyleSheet('color: black; background-color: rgb(0,211,0); border: 2px solid black')
          
    def disconnect_motor(self):
        self.enable_btn.setChecked(False)
        self.disable_btn.setChecked(False)      
        self.motor_status.setText('IDLE')
        self.motor_status.setStyleSheet('color: black; background-color: rgb(211,211,211); border: 2px solid black')
                                      
    def enable_motor(self):
        self.enable_btn.setChecked(True)
        self.disable_btn.setChecked(False)
        self.motor_status.setText('ENABLED')
        self.motor_status.setStyleSheet('color: black; background-color: rgb(0,211,0); border: 2px solid black')
    
            
    def disable_motor(self):
        self.disable_btn.setChecked(True)
        self.enable_btn.setChecked(False)
        self.motor_status.setText('DISABLED')
        self.motor_status.setStyleSheet('color: black; background-color: rgb(255,0,0); border: 2px solid black')

        
    
    def do_nothing(self):
        pass      
        
    def start_stepper(self):
        if self.ser.isOpen() == False:
            self.ser.open()
        self.ser.write(chr(255))
        
    def stop_stepper(self):
        self.ser.close()
        self.ser.open()
    
    

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
            self.ser.close()
        else:
            event.ignore()  
            
    def save(self):
        fname = str(QFileDialog.getSaveFileName(self,'Select Save File'))
        #Make sure there is the appropriate extension
        if fname=='':
            pass
        elif fname.endswith('.fits'):
            self.write_fits(fname)
        else:
            QMessageBox.warning(self, 'Error', 'Please provide a .fits extension')
            self.save()
                  
    def write_fits(self,fname):
            #Now write the FITS files
            prihdr = pyfits.Header()
            prihdr['NPRESS'] = 'hello'#(len(pressures),'number of pressures, (mbar)')
            prihdr['NTEMPS'] = 'hello3'#(len(temperatures),'number of temperatures, (K)')        
            prihdr['NG'] = 'bye' #(ng,'number of quadrature nodes, weights')
            prihdr['NLAM'] = 'bye' #(len(wavelength),'number of wavelength, (um)')
            prihdr['SHIFT'] = 'bye' #(shift,'wavelength shift, (nm)')
            
            prihdu = pyfits.PrimaryHDU(np.array([1,1]),header=prihdr)
    
            hdulist = pyfits.HDUList([prihdu])
            hdulist.writeto(fname,clobber=True) 
            

######################################################################################################################
###########################################  GUI Functions  ##########################################################
######################################################################################################################   
    def position_filter(self):
        filt_wheel = FilterWheelDriver(p=2,baud=115200)
        filt_wheel.setPos(int(self.filtpos_combo.currentText()[-1]))
        filt_wheel.close()

    def open_save(self):
        
        directory = QFileDialog.getSaveFileName(self,'Select Save File')
        self.save_line.setText(directory.replace('\\','\\'))
                
    def on_submit(self):
        self.position_filter()


        
                            
def main():
    app = QApplication(sys.argv)
    window = Window()
    window.showMaximized()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()