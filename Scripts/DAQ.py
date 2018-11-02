from DAQCode import MultiChannelAnalogInput
from numpy import linspace
rate = 50000
samples = 500000
test = MultiChannelAnalogInput(rate,samples,["Dev1/ai0"])
y = []
y = linspace(0,10,samples)
x = []
for k in range(6):
    test.configure()
    x.append(test.read().tolist()) 