#!/usr/bin/python3
import time
from sorensenPower import sorensenPower

power = sorensenPower(portName="/dev/tty.serial1")
print("Model: {}".format(power.getModel()))
print("Serial Number: {}".format(power.getSerialNumber()))

power.setOutputVoltage(0.0)
power.setOutputCurrent(5.0)

print("Ramping from 0.0v to 4.0v over 2 seconds.")
power.setOutputVoltageRamp(4.0, 2.0)

end = time.monotonic() + 100

while (time.monotonic() < end):
    voltage = power.getOutputVoltage()
    current = power.getOutputCurrent()
    if abs(current) < 0.001:
        resistance = 1e10
    else:
        resistance = voltage / current

    print("Voltage: {:1.03f}, Current: {:1.03f}, Resistance: {:1.03f}".format(voltage, current, resistance))

power.setOutputVoltage(0.0)
