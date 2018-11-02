from DAQCode import MultiChannelAnalogInput
num = 0
rate = 1000
samples = 1000
test = MultiChannelAnalogInput(rate,samples,["Dev1/ai0"])
test.configure()
data = test.read()

import numpy as np
t = np.linspace(0,samples/rate,samples)
np.save('C:/Users/Philip/Desktop/FTS_Software/Time_Constant/data_%03d.npy'%num,np.stack((t,data)))