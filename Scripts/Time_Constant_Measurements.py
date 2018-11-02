from DAQCode import MultiChannelAnalogInput
import glob

time = 10 #[s]
rate = 40e3 #[Hz]

num = len(glob.glob('C:/Users/Philip/Desktop/FTS_Software/Time_Constant/*.npy'))
samples = int(time*rate)
test = MultiChannelAnalogInput(rate,samples,["Dev1/ai0"])
test.configure()
data = test.read()

import numpy as np
t = np.linspace(0,samples/rate,samples)
np.save('C:/Users/Philip/Desktop/FTS_Software/Time_Constant/data_%03d.npy'%num,np.stack((t,data)))

from matplotlib import pyplot as plt
fig,ax = plt.subplots(figsize=(32,23))
ax.plot(t,data)
ax.set_xlabel('Time [s]',fontsize=32)
ax.set_ylabel('Signal [V]',fontsize=32)
ax.tick_params(labelsize=22)
plt.show()

#Notes kept here for the contents of each file
'''
data_000:
    - 40 Hz
    - 10 second integration time, 40kHz sampling rate
    - Gain set to 200
    - Chopper next to detector looking mainly at room with heat lamp at a distance

data_001:
    - 10 Hz
    - Same as data_000 otherwise
    
data_002:
    - 4 Hz
    - Same otherwise
    
data_003:
    - 100 Hz
    - Same otherwise
    
data_004:
    - 160 Hz
    - Same otherwise
    
data_005:
    - 200 Hz
    - Same otherwise
    
    
data_006:
    - 40 Hz
    - 10 second integration time, 40kHz sampling rate
    - Gain raised to 1000
    - Same otherwise
    
data_007:
    - 10 Hz
    - Same as data_006 otherwise
    
data_008:
    - 4 Hz
    - Same otherwise
    
data_009:
    - 100 Hz
    - Same otherwise
    
data_010:
    - 160 Hz
    - Same otherwise
    
data_011:
    - 200 Hz
    - Same otherwise
'''