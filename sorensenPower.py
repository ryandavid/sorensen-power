#!/usr/bin/python

import serial
import time
import struct

# Assumes the following settings for the DCS M9 RS-232 Interface
# Baud-rate = 19200
# Hardware Flow Control = None

class sorensenPower:

	DEFAULT_READ_SIZE = 200
	DEFAULT_SLEEP_TIME = 0.000
	DEFAULT_TIMEOUT = 0.075

	# List of commands
	COMMAND_IDN 					= '*IDN?'

	COMMAND_MEASURE_CURRENT			= ':MEAS:CURR?'
	COMMAND_MEASURE_VOLTAGE 		= ':MEAS:VOLT?'

	COMMAND_SET_VOLTAGE 			= ':SOUR:VOLT '

	COMMAND_SET_CURRENT 			= ':SOUR:CURR '

	COMMAND_GET_STATUS 				= ':SOUR:STAT:BLOC?'

	COMMAND_RETURN_LOCAL			= ':SYST:LOCAL ON'

	def __init__( self, portName='/dev/ttyUSB0', baudrate=19200 ):
		self.portName = portName
		self.baudrate = baudrate

		self.port = serial.Serial() # self.portName, baudrate, timeout=0, dsrdtr=True)
		self.port.baudrate = self.baudrate
		#self.port.dsrdtr=True;
		self.port.port = self.portName
		self.port.timeout = self.DEFAULT_TIMEOUT
		self.port.rts = True
		self.port.dtr = True

		self.model = None
		self.serialNumber = None
		self.maxVoltage = None
		self.maxCurrent = None

		self.connect()

	def connect( self ):
		success = False

		if( self.port.isOpen() == False ):
			self.port.open()

		self.getStatus()

		success = self.port.isOpen()

		return success

	def disconnect( self, returnToLocal=True ):
		if( returnToLocal == True ):
			self.writeCommand( self.COMMAND_RETURN_LOCAL )

		success = False

		if( self.port.isOpen() == True ):
			self.port.close()
			success = True

		return success

	def getModel( self, forceUpdate=False ):
		if( (self.model == None) | forceUpdate ):
			self.getStatus()

		return self.model

	def getSerialNumber( self, forceUpdate=False ):
		if( (self.serialNumber == None) | forceUpdate ):
			self.getStatus()

		return self.serialNumber

	def getMaxVoltage( self, forceUpdate=False ):
		if( (self.maxVoltage == None) | forceUpdate ):
			self.getStatus()

		return self.maxVoltage

	def getMaxCurrent( self, forceUpdate=False ):
		if( (self.maxCurrent == None) | forceUpdate ):
			self.getStatus()

		return self.maxCurrent

	def writeCommand( self, command ):
		success = False

		if( self.port.isOpen() ):
			# Automatically wait some time before bombing the instrument
			time.sleep( self.DEFAULT_SLEEP_TIME )
			self.port.write( command )
			self.port.write( '\r' )

			success = True

		return success

	def readResult( self, length=None ):
		data = None

		if( length == None ):
			data = self.port.read(self.DEFAULT_READ_SIZE)
		else:
			data = self.port.read(length)

		return data

	def getIdentification( self ):
		self.writeCommand( self.COMMAND_IDN )

		identification = self.readResult()

		return identification.strip()

	def getOutputVoltage( self ):
		self.writeCommand( self.COMMAND_MEASURE_VOLTAGE )

		voltageASCII = self.readResult()
		voltage = float( voltageASCII.strip() )

		return voltage

	def getOutputCurrent( self ):
		self.writeCommand( self.COMMAND_MEASURE_CURRENT )

		currentASCII = self.readResult()
		current = float( currentASCII.strip() )

		return current

	def setOutputVoltage( self, voltage ):
		success = False

		if( (voltage >= 0) & (voltage <= self.maxVoltage) ):
			self.writeCommand( self.COMMAND_SET_VOLTAGE + str(voltage) )
			success = True

		return success

	def setOutputCurrent( self, current ):
		success = False

		if( (current >= 0) & (current <= self.maxCurrent) ):
			self.writeCommand( self.COMMAND_SET_CURRENT + str(current) )
			success = True

		return success

	def getStatus( self ):
		status = None

		self.writeCommand( self.COMMAND_GET_STATUS )
		statusASCII = self.readResult().strip().split(',')
		
		# Doesn't seem to follow the interface spec
		if( len(statusASCII) == 23 ):
			statusRegister = int( statusASCII[3] )
			overTemperature = bool((statusRegister >> 4) & 0x01)
			overVoltage 	= bool((statusRegister >> 3) & 0x01)
			constantCurrent	= bool((statusRegister >> 1) & 0x01)
			constantVoltage = bool((statusRegister >> 0) & 0x01)

			status = {
				'channelNumber'		: int( statusASCII[0] ),
				'onlineStatus'		: int( statusASCII[1] ),
				'statusFlags'		: int( statusASCII[2] ),
				'statusRegister'	: statusRegister,
				'accumulatedStatus'	: int( statusASCII[4] ),
				'faultMask'			: int( statusASCII[5] ),
				'faultRegister'		: int( statusASCII[6] ),
				'errorRegister'		: int( statusASCII[7] ),
				'overTemperature'	: overTemperature,
				'overVoltage'		: overVoltage,
				'constantCurrent'	: constantCurrent,
				'constantVoltage'	: constantVoltage,
				'serialNumber'		: statusASCII[8],
				'voltageCapability'	: float( statusASCII[9] ),
				'currentCapability' : float( statusASCII[10] ),
				'overVoltage'		: float( statusASCII[11] ),
				'voltageDacGain'	: float( statusASCII[12] ),
				'voltageDacOffset'	: float( statusASCII[13] ),
				'currentDacGain'	: float( statusASCII[14] ),
				'currentDacOffset'	: float( statusASCII[15] ),
				'protectionDacGain'	: float( statusASCII[16] ),
				'protectionDacOffset': float( statusASCII[17] ),
				'voltageAdcGain'	: float( statusASCII[18] ),
				'voltageAdcOffset'	: float( statusASCII[19] ),
				'currentAdcGain'	: float( statusASCII[20] ),
				'currentAcOffset'	: float( statusASCII[21] ),
				'model'				: statusASCII[22]
			}

			self.model = status['model']
			self.serialNumber = status['serialNumber']
			self.maxCurrent = status['currentCapability']
			self.maxVoltage = status['voltageCapability']

		return status
