#!/usr/bin/python

from sorensenPower import sorensenPower

power = sorensenPower()
print "Model: " + power.getModel()
print "Serial Number: " + power.getSerialNumber()
print "Voltage: {0}".format( power.getOutputVoltage() )
print "Current: {0}".format( power.getOutputCurrent() )

#power.setOutputVoltage( 3.21 )
#power.setOutputCurrent( 0.25 )

#print power.getStatus()

power.disconnect()